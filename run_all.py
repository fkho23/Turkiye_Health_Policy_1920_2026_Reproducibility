#!/usr/bin/env python3
"""run_all.py — Makaledeki bütün hesaplamalı sonuçları tek komutla yeniden üretir.

Tam yeniden üretim (özgün kaynaklardan başlayarak):
    python run_all.py --kaynaklar sources                 # PDF'ler sources/ altında (s00 ile indirilebilir)
    python run_all.py --kaynaklar sources --ocr calistir  # 9. Plan OCR'ını da yeniden yapar (yavaş; sürüme duyarlı)
Hazır türetilmiş metinlerden (metin çıkarımı atlanır):
    python run_all.py --turetilmis <klasör>               # korpus_paragraflar.csv, Hukumet_Programlari_TXT/, Karsilastirma_TXT/, OCR/
Seçenekler:
    --cikti <klasör>   çıktı klasörü (varsayılan: outputs). Var olan bir klasör verilirse içeriği silinmez; yeni/boş klasör önerilir.
    --ocr-metni <dosya> 9. Plan OCR metni (OCR yeniden çalıştırılmayacaksa). Verilmezse <türetilmiş>/OCR altında aranır.
    --form1/--form2 <xlsx>  doldurulmuş insan değerlendirme formları (verilirse kodlayıcı uyumu hesaplanır).
Her adımın süresi ve sonucu <çıktı>/calistirma_gunlugu.json, yazılım ortamı <çıktı>/ortam.json dosyasına yazılır."""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time
from importlib import metadata
from pathlib import Path

PKG = Path(__file__).resolve().parent
CODE = PKG / 'code'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def tool(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return (r.stdout + r.stderr).strip().splitlines()[0]
    except Exception as e:
        return f'yok ({type(e).__name__})'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kaynaklar'); ap.add_argument('--turetilmis'); ap.add_argument('--cikti', default=str(PKG / 'outputs'))
    ap.add_argument('--ocr', choices=['calistir', 'hazir'], default='hazir'); ap.add_argument('--ocr-metni')
    ap.add_argument('--form1'); ap.add_argument('--form2')
    a = ap.parse_args()
    out = Path(a.cikti).resolve(); out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, REPRO_OUT=str(out), PYTHONHASHSEED='0', MPLBACKEND='Agg')
    if a.kaynaklar: env['REPRO_SOURCES'] = str(Path(a.kaynaklar).resolve())
    if a.turetilmis:
        env['REPRO_DERIVED'] = str(Path(a.turetilmis).resolve()); extract = False
    else:
        if not a.kaynaklar: sys.exit('Ya --kaynaklar (özgün PDF klasörü) ya da --turetilmis (hazır metinler) verilmelidir.')
        env['REPRO_DERIVED'] = str(out / 'derived_text'); extract = True
    derived = Path(env['REPRO_DERIVED'])
    # ortam kaydı
    pk = {}
    for p in ['pandas', 'numpy', 'scipy', 'matplotlib', 'openpyxl']:
        try: pk[p] = metadata.version(p)
        except Exception: pk[p] = 'yok'
    ortam = dict(zaman=time.strftime('%Y-%m-%d %H:%M:%S'), python=sys.version, platform=platform.platform(), paketler=pk,
                 pdftotext=tool(['pdftotext', '-v']), pdfinfo=tool(['pdfinfo', '-v']), pdftoppm=tool(['pdftoppm', '-v']), tesseract=tool(['tesseract', '--version']),
                 parametreler=json.load(open(PKG / 'config' / 'params.json', encoding='utf-8')), secenekler=vars(a))
    json.dump(ortam, open(out / 'ortam.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    steps = []
    if extract:
        steps += [('Kaynak PDF doğrulama (SHA-256)', ['s00_kaynaklari_indir.py', '--dogrula'], False),
                  ('Hükümet programı metin çıkarımı', ['s01_metin_cikarimi_hukumet_programlari.py'], True)]
        if a.ocr == 'calistir': steps.append(('9. Plan OCR', ['s02b_ocr_plan9.py'], True))
        steps.append(('Plan ve yıllık program metin çıkarımı', ['s02_metin_cikarimi_plan_program.py'], True))
    steps += [('Hükümet programı analizleri (sözlük, dönem, tür, tema, LL)', ['s03_analiz_hukumet_programlari.py'], True),
              ('Plan ve yıllık program metrikleri', ['s04_karsilastirma_metrikleri.py'], True),
              ('Sağlamlık testleri ve program–plan eşleştirmesi', ['s05_saglamlik_testleri.py'], True),
              ('Etki büyüklüğü, bootstrap, Holm, basıklık', ['s06_ek_testler.py'], True),
              ('2018–2026 yıllık programlar', ['s07_cumhurbaskanligi_donemi.py'], True),
              ('Şekil 1–4', ['s08_sekiller_1_4.py'], True),
              ('Cümle düzeyi veri seti', ['s09_cumle_veri_seti.py'], True),
              ('Revizyon analizleri (Tablo 5, plan düzeyi, permütasyon, Holm+uzunluk, L-basıklık, DSÖ, LL)', ['s10_revizyon_analizleri.py'], True),
              ('Şekil 5', ['s11_who_sekil.py'], True),
              ('Terim sayımları', ['s16_terim_sayimlari.py'], True),
              ('Kör doğrulama formları', ['s12_dogrulama_formlari.py'], True),
              ('Makale tabloları ve eşleştirme', ['s14_makale_tablolari.py'], True),
              ('Makaleyle karşılaştırma', ['s15_makale_ile_karsilastir.py'], False)]
    if a.form1 and a.form2: steps.append(('Kodlayıcı uyumu', ['s13_kodlayici_uyumu.py', '--d1', a.form1, '--d2', a.form2], True))
    log = []
    for name, cmd, must in steps:
        if cmd[0] == 's02_metin_cikarimi_plan_program.py' and a.ocr == 'hazir':
            ocr_hedef = derived / 'OCR' / 'DEVPLAN_09_Dokuzuncu_Kalkinma_Plani_2007_2013_OCR.txt'
            if a.ocr_metni and not ocr_hedef.exists():
                ocr_hedef.parent.mkdir(parents=True, exist_ok=True); shutil.copy(a.ocr_metni, ocr_hedef)
        t0 = time.time(); print(f'\n=== {name} ===', flush=True)
        r = subprocess.run([sys.executable, str(CODE / cmd[0])] + cmd[1:], env=env, cwd=str(PKG), capture_output=True, text=True)
        (out / 'gunluk').mkdir(exist_ok=True); open(out / 'gunluk' / f'{cmd[0][:-3]}.log', 'w', encoding='utf-8').write(r.stdout + '\n--- stderr ---\n' + r.stderr)
        log.append(dict(adim=name, betik=cmd[0], sure_sn=round(time.time() - t0, 1), donus_kodu=r.returncode))
        print(f'  -> dönüş kodu {r.returncode}, {log[-1]["sure_sn"]} sn', flush=True)
        if r.returncode != 0:
            print(r.stderr[-2000:])
            if must:
                json.dump(log, open(out / 'calistirma_gunlugu.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1); sys.exit(f'Adım başarısız: {name}')
    # türetilmiş metinlerin özgün analizdekiyle karşılaştırılması
    beklenen = PKG / 'inventory' / 'turetilmis_metin_ozetleri.csv'
    if beklenen.exists():
        import csv
        rows = list(csv.DictReader(open(beklenen, encoding='utf-8-sig'))); sonuc = []
        for r in rows:
            p = derived / r['Goreli_Yol']
            sonuc.append(dict(Dosya=r['Goreli_Yol'], Durum=('AYNI' if p.exists() and sha(p) == r['SHA256'] else ('YOK' if not p.exists() else 'FARKLI'))))
        with open(out / 'turetilmis_metin_karsilastirma.csv', 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['Dosya', 'Durum']); w.writeheader(); w.writerows(sonuc)
        n_ayni = sum(s['Durum'] == 'AYNI' for s in sonuc); print(f'\nTüretilmiş metinler: {n_ayni}/{len(sonuc)} dosya özgün analizdekiyle bayt düzeyinde aynı.')
        log.append(dict(adim='Türetilmiş metin özet karşılaştırması', ayni=n_ayni, toplam=len(sonuc)))
    json.dump(log, open(out / 'calistirma_gunlugu.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\nBitti. Çıktılar: {out}\nDoğrulama raporu: {out / "DOGRULAMA_RAPORU.md"}')


if __name__ == '__main__':
    main()

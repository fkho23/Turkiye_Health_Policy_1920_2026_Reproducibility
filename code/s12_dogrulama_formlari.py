"""s12 — İki bağımsız insan değerlendirici için kör doğrulama formları (gerçek korpus cümleleri).
Örnekleme (seed: params.json -> seeds.dogrulama_formu):
  Bölüm A (sağlık tespiti): 4 tabaka × (25 sözlük-pozitif + 15 sözlük-negatif) = 160 cümle.
     Tabakalar: 1) hükümet programları 1920–1945, 2) hükümet programları 1946–2016, 3) kalkınma planları, 4) yıllık programlar 2018–2026.
     Havuz: en az 4 kelimelik cümleler. Negatifler korpus düzeyi ağırlıklı recall tahmini için ayrı çekilir (ağırlıklar anahtar dosyasında).
  Bölüm B (tema): her tema için sözlüğün temaya atadığı cümlelerden en çok 20 (belge türleri arasında dengeli); yinelenen cümleler bir kez alınır.
Her kayıt: benzersiz kayıt ID, kararlı cümle anahtarı, belge adı/türü/tarihi, kaynak dosya, PDF sayfası, basılı sayfa (TBMM ciltleri), özgün cümle ve bağlamı.
Formlarda sözlük kararı ve diğer değerlendiricinin kararı YOKTUR. İki form aynı kayıtları farklı sırada içerir.
Çıktılar (outputs/dogrulama/):
  Degerlendirici_1_Kor_Form.xlsx, Degerlendirici_2_Kor_Form.xlsx  -> değerlendiricilere gönderilir
  _ANAHTAR_Sozluk_Kararlari_GONDERMEYIN.xlsx                       -> sözlük kararları, tabaka ağırlıkları, sayfa bulma kaydı
Sayfa numarası, cümlenin harf dizisinin (boşluk/tire/noktalama çıkarılmış) kaynak PDF'in sayfa metinlerinde aranmasıyla bulunur;
bulunamazsa 'bulunamadı' yazılır (çok sayfaya taşan cümlelerde ilk sayfa verilir)."""
import os, re, sys, subprocess
import numpy as np, pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, Alignment, PatternFill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from sozlukler import norm, mask, is_h, words, TRE, TLABEL, DROP, sentences, THEMES

TK = list(TLABEL); SEED = seed('dogrulama_formu')
D = pd.read_csv(DOCS); SR = pd.read_csv(SRCS).set_index('Kaynak_ID')
P = pd.read_csv(PARAS); P = P[~P['Metin'].str.contains(DROP)]
rows = []
for _, d in D.iterrows():
    if d.Tur == 'Hükümet programı':
        paras = P[P.Hukumet_ID == d.Belge_ID].sort_values('Paragraf_No')[['Paragraf_No', 'Metin']].values.tolist()
    else:
        txt = open(os.path.join(TXT_COMP, f'{d.Belge_ID}.txt'), encoding='utf-8').read().split('\n\n')
        paras = [[i + 1, t] for i, t in enumerate(txt)]
    for pno, p in paras:
        ss = sentences(p)
        for i, c in enumerate(ss):
            if len(words(c)) < 4: continue
            h = is_h(c); n = mask(norm(c))
            rows.append(dict(Belge_ID=d.Belge_ID, Cumle_Anahtari=f'{d.Belge_ID}|p{int(pno)}|c{i + 1}', Belge_adi=d.Ad, Belge_turu=d.Tur, Belge_tarihi=d.Belge_Tarihi,
                             Yil=int(d.Baslangic), Cumle=c, Onceki=ss[i - 1] if i > 0 else '', Sonraki=ss[i + 1] if i + 1 < len(ss) else '',
                             Sozluk_saglik=int(h), **{k: int(h and len(TRE[k].findall(n)) > 0) for k in TK}))
C = pd.DataFrame(rows)
C['Tabaka'] = np.where(C.Belge_turu == 'Hükümet programı', np.where(C.Yil < 1946, '1_HP_1920_1945', '2_HP_1946_2016'),
                       np.where(C.Belge_turu == 'Kalkınma planı', '3_Kalkinma_plani', '4_Yillik_program'))
A_rows, W = [], []
for t, g in C.groupby('Tabaka'):
    pos = g[g.Sozluk_saglik == 1]; neg = g[g.Sozluk_saglik == 0]
    sp = pos.sample(min(25, len(pos)), random_state=SEED); sn = neg.sample(15, random_state=SEED)
    A_rows += [sp, sn]
    W.append(dict(Tabaka=t, Havuz_pozitif=len(pos), Havuz_negatif=len(neg), Orneklem_pozitif=len(sp), Orneklem_negatif=len(sn)))
SA = pd.concat(A_rows).sample(frac=1, random_state=SEED).reset_index(drop=True); SA['Kayit_ID'] = [f'A{i + 1:03d}' for i in range(len(SA))]
B_rows = []
for k in TK:
    g = C[C[k] == 1]
    if len(g) <= 20: s = g
    else:
        parts = []; per = int(np.ceil(20 / g.Belge_turu.nunique()))
        for _, gt in g.groupby('Belge_turu'): parts.append(gt.sample(min(per, len(gt)), random_state=SEED))
        s = pd.concat(parts)
        if len(s) > 20: s = s.sample(20, random_state=SEED)
        if len(s) < 20: s = pd.concat([s, g.drop(s.index).sample(20 - len(s), random_state=SEED)])
    B_rows.append(s.assign(Ornekleme_temasi=TLABEL[k]))
SB = pd.concat(B_rows); SB = SB[~SB.index.duplicated()].sample(frac=1, random_state=SEED).reset_index(drop=True)
SB['Kayit_ID'] = [f'B{i + 1:03d}' for i in range(len(SB))]

# ---- sayfa bulma
key = lambda s: re.sub(r'[\W_]+', '', norm(s))
_pages = {}


def pages_of(bid):
    if bid in _pages: return _pages[bid]
    d = D.set_index('Belge_ID').loc[bid]
    if bid == 'DEVPLAN-09':
        f = os.path.join(OCR_DIR, 'DEVPLAN_09_Dokuzuncu_Kalkinma_Plani_2007_2013_OCR.txt')
        raw = open(f, encoding='utf-8', errors='ignore').read() if os.path.exists(f) else ''
        npdf = int([l for l in subprocess.run(['pdfinfo', str(SOURCES / SR.loc['DEVPLAN-09', 'Goreli_Yol'])], capture_output=True, text=True).stdout.splitlines() if l.startswith('Pages')][0].split()[-1]) \
            if (SOURCES / SR.loc['DEVPLAN-09', 'Goreli_Yol']).exists() else 0
        # s02b her sayfayı tek \f ile bitirir; özgün arşiv OCR metninde sayfalar \f\f ile ayrılmıştır
        pg = raw.split('\f\f') if npdf and raw.count('\f') >= 2 * npdf else raw.split('\f') if raw else []
        res = [(i + 1, key(t)) for i, t in enumerate(pg)]
    else:
        pdf = SOURCES / SR.loc[d.Kaynak_ID, 'Goreli_Yol']
        if not pdf.exists(): _pages[bid] = None; return None
        a, b = (int(d.PDF_Sayfa_Bas), int(d.PDF_Sayfa_Bit)) if pd.notna(d.PDF_Sayfa_Bas) else (1, 99999)
        args = ['pdftotext'] + (['-layout'] if d.Tur == 'Hükümet programı' else []) + ['-f', str(a)] + (['-l', str(b)] if b < 99999 else []) + [str(pdf), '-']
        raw = subprocess.run(args, capture_output=True).stdout.decode('utf-8', 'ignore')
        if raw.count('õ') > 1000: raw = raw.replace('õ', 'ı')   # s02 ile aynı yazı tipi onarımı (8. Plan)
        pg = raw.split('\f')
        res = [(a + i, key(t)) for i, t in enumerate(pg)]
    _pages[bid] = res; return res


def find_page(row):
    ps = pages_of(row.Belge_ID)
    if not ps: return 'kaynak PDF gerekli', ''
    k = key(row.Cumle)
    for L in (60, 35, 20):
        frag = k[:L]
        if len(frag) < 12: break
        for pno, t in ps:
            if frag in t:
                d = D.set_index('Belge_ID').loc[row.Belge_ID]
                bas = ''
                if pd.notna(d.Basili_Sayfa_Bas) and pd.notna(d.PDF_Sayfa_Bas): bas = int(pno - int(d.PDF_Sayfa_Bas) + int(d.Basili_Sayfa_Bas))
                return pno, bas
    return 'bulunamadı', ''


for S_ in (SA, SB):
    pr = S_.apply(find_page, axis=1); S_['PDF_sayfa'] = [x[0] for x in pr]; S_['Basili_sayfa'] = [x[1] for x in pr]
    S_['Kaynak_dosya'] = S_.Belge_ID.map(lambda b: SR.loc[D.set_index('Belge_ID').loc[b, 'Kaynak_ID'], 'Goreli_Yol'])

WHO = ['Hizmet sunumu', 'Sağlık insan gücü', 'Sağlık bilgi sistemleri', 'Tıbbi ürünler ve teknoloji', 'Sağlık finansmanı', 'Liderlik ve yönetişim', 'Hiçbiri']
TSH = {k: f'T{i + 1:02d} {TLABEL[k]}' for i, k in enumerate(TK)}
info = ['Kayit_ID', 'Cumle_Anahtari', 'Belge_adi', 'Belge_turu', 'Belge_tarihi', 'Kaynak_dosya', 'PDF_sayfa', 'Basili_sayfa', 'Onceki', 'Cumle', 'Sonraki']
talimat = pd.DataFrame({'Talimat': [
    'Bu form, Türkiye\'de hükümet programları, kalkınma planları ve yıllık programlarda sağlık içeriğinin sözlük temelli tespitini bağımsız olarak doğrulamak içindir.',
    'Formu tek başınıza doldurunuz. Diğer değerlendiriciyle, araştırmacıyla veya otomatik sınıflandırma sonuçlarıyla karşılaştırma yapmayınız; bu formda otomatik karar yer almaz.',
    'Bölüm A: Her cümle için "Saglik_icerigi" sütununa 1 (insan sağlığı, sağlık hizmetleri, sağlık kurumları, sağlık personeli, ilaç, hastalık, sağlık finansmanı vb.) veya 0 yazınız. '
    'Hayvan/bitki sağlığı, zirai ilaç ve mecazi kullanımlar ("ekonominin sıhhati") 0 sayılır. Kararsız kaldığınızda yine 0/1 seçip "Sinirda" sütununa 1 yazınız.',
    'Bölüm B: Her cümle için 14 temanın her birine ilgiliyse 1, değilse 0 yazınız (birden fazla tema olabilir). Ardından ağırlıklı ilgili tek DSÖ yapı taşını listeden seçiniz.',
    'Kararı ortadaki cümle için veriniz; önceki/sonraki cümleler bağlam içindir. Gerekirse kaynak dosyanın belirtilen PDF sayfasına bakabilirsiniz. OCR/biçim bozukluklarını düzeltmeyiniz.',
    'Tema ve yapı taşı tanımları "Kod_Kitabi" ve "DSO_Tanimlari" sayfalarındadır. Tamamlanan formu adınız ve tarihle iade ediniz.',
    'Değerlendirici adı: ____________________   Tarih: ____________   Değerlendirme süresi (saat): ______']})
codebook = pd.DataFrame([(TSH[k], ', '.join(re.sub(r'\\b|\(\?:|\)|\?|\\s', '', x).replace('|', '/') for x in THEMES[k][:10])) for k in TK],
                        columns=['Tema', 'Örnek ifadeler (yalnızca tanım için; karar cümlenin anlamına göre verilir)'])
who_def = pd.DataFrame({'DSÖ yapı taşı': WHO[:-1], 'Kısa tanım': [
    'Koruyucu, birinci basamak, hastane, acil, ana-çocuk vb. sağlık hizmetlerinin sunumu ve örgütlenmesi', 'Sağlık personelinin sayısı, eğitimi, dağılımı, istihdamı',
    'Sağlık bilgi sistemleri, kayıt, veri, dijital sağlık', 'İlaç, aşı, tıbbi cihaz, sağlık teknolojisi ve sanayii', 'Sigorta, finansman, ödeme, geri ödeme, finansal koruma',
    'Mevzuat, teşkilat, düzenleme, denetim, kalite, kamu-özel ilişkileri, reform ve koordinasyon']})


def form(path, order_seed):
    FA = SA.sample(frac=1, random_state=order_seed)[info].copy()
    FA['Saglik_icerigi (1/0)'] = ''; FA['Sinirda (1)'] = ''; FA['Aciklama'] = ''
    FB = SB.sample(frac=1, random_state=order_seed)[info].copy()
    for k in TK: FB[TSH[k]] = ''
    FB['DSO_yapi_tasi'] = ''; FB['Sinirda (1)'] = ''; FB['Aciklama'] = ''
    with pd.ExcelWriter(path, engine='openpyxl') as w:
        talimat.to_excel(w, sheet_name='Talimat', index=False); FA.to_excel(w, sheet_name='A_Saglik_Tespiti', index=False)
        FB.to_excel(w, sheet_name='B_Tema_ve_DSO', index=False); codebook.to_excel(w, sheet_name='Kod_Kitabi', index=False); who_def.to_excel(w, sheet_name='DSO_Tanimlari', index=False)
    wb = load_workbook(path)
    for sh in ['A_Saglik_Tespiti', 'B_Tema_ve_DSO']:
        ws = wb[sh]; hdr = [c.value for c in ws[1]]
        for c in ws[1]: c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical='top'); c.fill = PatternFill('solid', fgColor='DDEBF7')
        for col, wd in zip('ABCDEFGHIJK', [8, 18, 26, 18, 12, 30, 8, 8, 35, 60, 35]): ws.column_dimensions[col].width = wd
        for row in ws.iter_rows(min_row=2):
            for c in row[8:11]: c.alignment = Alignment(wrap_text=True, vertical='top')
        dv = DataValidation(type='list', formula1='"0,1"', allow_blank=True); ws.add_data_validation(dv)
        for j, h in enumerate(hdr, start=1):
            L = ws.cell(1, j).column_letter
            if h and (h.startswith('Saglik_icerigi') or h.startswith('Sinirda') or re.match(r'T\d\d ', h)): dv.add(f'{L}2:{L}{ws.max_row}')
            if h == 'DSO_yapi_tasi':
                dv2 = DataValidation(type='list', formula1='"' + ','.join(WHO) + '"', allow_blank=True); ws.add_data_validation(dv2); dv2.add(f'{L}2:{L}{ws.max_row}')
        ws.freeze_panes = 'K2'
    wb['Talimat'].column_dimensions['A'].width = 150
    for c in wb['Talimat']['A']: c.alignment = Alignment(wrap_text=True)
    wb.save(path)


form(f'{VAL}/Degerlendirici_1_Kor_Form.xlsx', SEED + 1)
form(f'{VAL}/Degerlendirici_2_Kor_Form.xlsx', SEED + 2)
with pd.ExcelWriter(f'{VAL}/_ANAHTAR_Sozluk_Kararlari_GONDERMEYIN.xlsx') as w:
    SA[['Kayit_ID', 'Cumle_Anahtari', 'Belge_ID', 'Tabaka', 'Sozluk_saglik', 'PDF_sayfa']].to_excel(w, sheet_name='A_Sozluk', index=False)
    SB[['Kayit_ID', 'Cumle_Anahtari', 'Belge_ID', 'Belge_turu', 'Ornekleme_temasi', 'PDF_sayfa'] + TK].rename(columns=TSH).to_excel(w, sheet_name='B_Sozluk', index=False)
    pd.DataFrame(W).to_excel(w, sheet_name='Tabaka_Agirliklari', index=False)
    pd.DataFrame({'Bilgi': [f'seed={SEED}; form1 sırası seed+1, form2 sırası seed+2', f'A: {len(SA)} kayıt; B: {len(SB)} kayıt',
                            f"Sayfası bulunamayan: A {int((SA.PDF_sayfa == 'bulunamadı').sum())}, B {int((SB.PDF_sayfa == 'bulunamadı').sum())}"]}).to_excel(w, sheet_name='Bilgi', index=False)
print(pd.DataFrame(W).to_string()); print('A', len(SA), 'B', len(SB))
print('sayfası bulunamayan A:', int((SA.PDF_sayfa == 'bulunamadı').sum()), 'B:', int((SB.PDF_sayfa == 'bulunamadı').sum()))
print(SB.Ornekleme_temasi.value_counts().to_string())

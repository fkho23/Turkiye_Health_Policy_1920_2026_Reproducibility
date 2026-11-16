"""s13 — İnsan doğrulaması TAMAMLANDIKTAN SONRA çalıştırılır (run_all.py bu adımı formlar doluysa çalıştırır).
Kullanım:
  python code/s13_kodlayici_uyumu.py --d1 Degerlendirici_1_dolu.xlsx --d2 Degerlendirici_2_dolu.xlsx [--uzlasi Uzlasi.xlsx]
Hesaplananlar:
  1) Değerlendiriciler arası uyum: yüzde uyum ve Cohen kappa (A: sağlık 1/0; B: 14 tema ayrı ayrı; DSÖ yapı taşı çok kategorili).
  2) Sözlüğün geçerliliği: referans = uzlaşı dosyası (varsa) yoksa iki değerlendiricinin AYNI karar verdiği kayıtlar.
     A bölümünde precision, recall, F1; tabaka ağırlıklı (korpus düzeyi) ve ağırlıksız (örneklem içi) olarak.
     B bölümünde her tema için precision (temanın örneklendiği kayıtlarda) ve kappa.
Boş hücreler hesaba katılmaz; kullanılan n her sonuçla birlikte raporlanır. Bu kod hiçbir kararı varsaymaz veya doldurmaz.
Çıktı: outputs/dogrulama/kodlayici_uyumu_sonuclari.json ve .xlsx"""
import os, sys, json, argparse
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

KEY = f'{VAL}/_ANAHTAR_Sozluk_Kararlari_GONDERMEYIN.xlsx'
AC = 'Saglik_icerigi (1/0)'


def kappa(a, b):
    a = np.asarray(a); b = np.asarray(b)
    if len(a) == 0: return None, None
    po = float((a == b).mean()); cats = sorted(set(a) | set(b))
    pe = float(sum((a == k).mean() * (b == k).mean() for k in cats))
    return (round((po - pe) / (1 - pe), 3) if pe < 1 else None), round(po, 3)


def prf(ref, pred, w=None):
    ref = np.asarray(ref, int); pred = np.asarray(pred, int); w = np.ones(len(ref)) if w is None else np.asarray(w, float)
    tp = float((w * ((ref == 1) & (pred == 1))).sum()); fp = float((w * ((ref == 0) & (pred == 1))).sum())
    fn = float((w * ((ref == 1) & (pred == 0))).sum()); tn = float((w * ((ref == 0) & (pred == 0))).sum())
    p = tp / (tp + fp) if tp + fp else None; r = tp / (tp + fn) if tp + fn else None
    f1 = 2 * p * r / (p + r) if p and r else None
    rd = lambda x: None if x is None else round(x, 3)
    return dict(n=int(len(ref)), TP=round(tp, 1), FP=round(fp, 1), FN=round(fn, 1), TN=round(tn, 1), precision=rd(p), recall=rd(r), F1=rd(f1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--d1', required=True); ap.add_argument('--d2', required=True); ap.add_argument('--uzlasi')
    a = ap.parse_args()
    ka = pd.read_excel(KEY, 'A_Sozluk'); kb = pd.read_excel(KEY, 'B_Sozluk'); wt = pd.read_excel(KEY, 'Tabaka_Agirliklari')
    A1, A2 = (pd.read_excel(f, 'A_Saglik_Tespiti') for f in (a.d1, a.d2)); B1, B2 = (pd.read_excel(f, 'B_Tema_ve_DSO') for f in (a.d1, a.d2))
    tcols = [c for c in kb.columns if len(c) > 3 and c[0] == 'T' and c[1:3].isdigit()]
    out = {'not': 'Yalnızca doldurulmuş hücreler kullanılmıştır.'}
    # 1) değerlendiriciler arası
    m = A1[['Kayit_ID', AC]].merge(A2[['Kayit_ID', AC]], on='Kayit_ID', suffixes=('_1', '_2')).dropna()
    if len(m) == 0: sys.exit('Bölüm A boş: insan değerlendirmesi tamamlanmadan sonuç üretilemez.')
    k, po = kappa(m[f'{AC}_1'].astype(int), m[f'{AC}_2'].astype(int)); out['A_degerlendiriciler_arasi'] = dict(n=len(m), kappa=k, yuzde_uyum=po)
    mb = B1[['Kayit_ID'] + tcols + ['DSO_yapi_tasi']].merge(B2[['Kayit_ID'] + tcols + ['DSO_yapi_tasi']], on='Kayit_ID', suffixes=('_1', '_2'))
    filled = mb[[f'{c}_1' for c in tcols]].notna().any(axis=1) & mb[[f'{c}_2' for c in tcols]].notna().any(axis=1); mb = mb[filled]
    out['B_degerlendiriciler_arasi'] = {c: dict(zip(['kappa', 'yuzde_uyum'], kappa(mb[f'{c}_1'].fillna(0).astype(int), mb[f'{c}_2'].fillna(0).astype(int)))) | {'n': len(mb)} for c in tcols}
    dd = mb.dropna(subset=['DSO_yapi_tasi_1', 'DSO_yapi_tasi_2'])
    out['B_DSO_degerlendiriciler_arasi'] = dict(zip(['kappa', 'yuzde_uyum'], kappa(dd.DSO_yapi_tasi_1, dd.DSO_yapi_tasi_2))) | {'n': len(dd)}
    # 2) referans
    if a.uzlasi:
        RA = pd.read_excel(a.uzlasi, 'A_Saglik_Tespiti')[['Kayit_ID', AC]].dropna().rename(columns={AC: 'ref'}); kaynak = 'uzlaşı dosyası'
        RB = pd.read_excel(a.uzlasi, 'B_Tema_ve_DSO')[['Kayit_ID'] + tcols]
    else:
        RA = m[m[f'{AC}_1'] == m[f'{AC}_2']][['Kayit_ID', f'{AC}_1']].rename(columns={f'{AC}_1': 'ref'}); kaynak = 'iki değerlendiricinin aynı karar verdiği kayıtlar'
        RB = None
    out['referans'] = kaynak
    ra = RA.merge(ka, on='Kayit_ID'); ra['ref'] = ra.ref.astype(int)
    wt['w_pos'] = wt.Havuz_pozitif / wt.Orneklem_pozitif; wt['w_neg'] = wt.Havuz_negatif / wt.Orneklem_negatif
    ra = ra.merge(wt[['Tabaka', 'w_pos', 'w_neg']], on='Tabaka'); ra['w'] = np.where(ra.Sozluk_saglik == 1, ra.w_pos, ra.w_neg)
    out['A_sozluk_gecerlilik'] = {'orneklem_ici_agirliksiz': prf(ra.ref, ra.Sozluk_saglik), 'korpus_duzeyi_tabaka_agirlikli': prf(ra.ref, ra.Sozluk_saglik, ra.w),
                                  'tabakalar': {t: prf(g.ref, g.Sozluk_saglik) for t, g in ra.groupby('Tabaka')},
                                  'kappa_sozluk_referans': kappa(ra.ref, ra.Sozluk_saglik)[0]}
    res = {}
    for c in tcols:
        if RB is not None:
            r = RB[['Kayit_ID', c]].dropna().rename(columns={c: 'ref'})
        else:
            x = mb[mb[f'{c}_1'].fillna(0) == mb[f'{c}_2'].fillna(0)]; r = x[['Kayit_ID']].assign(ref=x[f'{c}_1'].fillna(0))
        r = r.merge(kb[['Kayit_ID', 'Ornekleme_temasi', c]], on='Kayit_ID'); r['ref'] = r.ref.astype(int)
        s = r[r.Ornekleme_temasi == c[4:]]
        res[c] = dict(n_ornekleme=len(s), precision=round(float(s.ref.mean()), 3) if len(s) else None, kappa_tum_B=kappa(r.ref, r[c].astype(int))[0], n_tum_B=len(r))
    out['B_sozluk_tema_gecerlilik'] = res
    json.dump(out, open(f'{VAL}/kodlayici_uyumu_sonuclari.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

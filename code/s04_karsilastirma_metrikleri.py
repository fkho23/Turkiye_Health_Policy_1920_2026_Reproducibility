"""s04 — Kalkınma planları ve yıllık programlar için sağlık payı ve tema isabetleri.
Özgün: 03_karsilastirma_korpuslari.py (ölçüm bölümü; mantık değiştirilmedi). Metin, s02 çıktısından okunur.
Çıktı: veri/karsilastirma_korpuslari_metrikleri.csv"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from sozlukler import norm, mask, HRE, TRE, TLABEL, words, hsent

D = pd.read_csv(DOCS)
rows = []
for _, d in D[D.Tur != 'Hükümet programı'].iterrows():
    paras = open(os.path.join(TXT_COMP, f'{d.Belge_ID}.txt'), encoding='utf-8').read().split('\n\n')
    tot = sum(len(words(p)) for p in paras)
    hs = 0; terms = 0; th = {k: 0 for k in TRE}
    for p in paras:
        for c in hsent(p):
            n = mask(norm(c)); terms += len(HRE.findall(n)); hs += len(words(c))
            for k, r in TRE.items(): th[k] += len(r.findall(n))
    rows.append(dict(ID=d.Belge_ID, Tur=d.Tur_Ozgun, Ad=d.Ad, Baslangic=int(d.Baslangic), Bitis=int(d.Bitis), Metin_Kaynagi=d.Metin_Kaynagi,
                     Toplam_Kelime=tot, Saglik_Cumle_Kelime=hs, **{'Saglik_Payi_%': round(hs / tot * 100, 2), 'Saglik_Terim_1000': round(terms / tot * 1000, 2)},
                     **{TLABEL[k]: v for k, v in th.items()}))
R_ = pd.DataFrame(rows).sort_values(['Tur', 'Baslangic'])
R_.to_csv(f'{V}/karsilastirma_korpuslari_metrikleri.csv', index=False, encoding='utf-8-sig')
print(R_[['ID', 'Tur', 'Baslangic', 'Metin_Kaynagi', 'Toplam_Kelime', 'Saglik_Payi_%', 'Saglik_Terim_1000']].to_string())

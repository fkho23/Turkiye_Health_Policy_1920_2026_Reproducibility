"""s11 — Özgün: 11_who_sekil.py (yalnızca yollar değişti).
11_who_sekil.py — Şekil 5: WHO altı yapı taşı boyutlarının dönem ve belge türlerine göre dağılımı (ısı haritası).
Değer: belge düzeyinde ortalama pay (%) = boyutun birincil olarak eşleştiği temalara düşen isabet / belgedeki tüm tema isabetleri.
Yalnızca en az bir tema isabeti olan belgeler ortalamaya girer; hücre altında n (isabetli belge / toplam belge) gösterilir."""
import os
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
O = RV; F = FIG
W = pd.read_csv(f'{O}/who_boyut_donem_tablosu.csv')
DIMS = ['Hizmet sunumu', 'Sağlık insan gücü', 'Sağlık bilgi sistemleri', 'Tıbbi ürünler ve teknoloji', 'Sağlık finansmanı', 'Liderlik ve yönetişim']
COLS = {'1920-1923 Meclis Hükümetleri': '1920–1923\nMeclis Hük.†', '1923-1946 Tek Parti': '1923–1946\nTek Parti', '1946-1960 Çok Partili Dönem': '1946–1960\nÇok Partili',
        '1960-1980 Planlı Dönem': '1960–1980\nPlanlı', '1980-2002 Neoliberal Dönüşüm': '1980–2002\nNeoliberal', '2002-2018 AK Parti Dönemi': '2002–2016\nAK Parti',
        'Planlar 1–3 (1963–1977)': '1.–3. Plan\n1963–1977', 'Planlar 4–6 (1979–1994)': '4.–6. Plan\n1979–1994', 'Planlar 7–9 (1996–2013)': '7.–9. Plan\n1996–2013',
        'Planlar 10–12 (2014–2028)': '10.–12. Plan\n2014–2028', 'Yıllık program 2018 (BK)': '2018\n(BK)', 'CB yıllık programları 2019–2026': 'CB yıllık\n2019–2026'}
W = W.set_index('Grup').loc[list(COLS)]
M = np.array([[W.loc[g, f'{d} | belge ort. pay %'] for g in COLS] for d in DIMS], float)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8})
fig, ax = plt.subplots(figsize=(11, 4.6))
im = ax.imshow(M, cmap='Blues', vmin=0, vmax=80, aspect='auto')
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M[i, j]
        ax.text(j, i, f'{v:.1f}'.replace('.', ','), ha='center', va='center', fontsize=7.5, color='white' if v > 45 else 'black')
ax.set_yticks(range(len(DIMS))); ax.set_yticklabels(DIMS)
lbl = [f"{COLS[g]}\n(n={int(W.loc[g,'Tema_isabeti_olan_belge'])}/{int(W.loc[g,'Belge'])})" for g in COLS]
ax.set_xticks(range(len(COLS))); ax.set_xticklabels(lbl, fontsize=7)
for x in (5.5, 9.5): ax.axvline(x, color='black', lw=1.6)
for x, t in [(2.5, 'Hükümet programları'), (7.5, 'Kalkınma planları'), (10.5, 'Yıllık programlar')]:
    ax.text(x, -0.85, t, ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_ylim(len(DIMS) - 0.5, -0.5)
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01); cb.set_label('Belge düzeyinde ortalama pay (%)')
fig.text(0.01, 0.005, 'Pay: boyuta birincil olarak eşlenen temaların isabeti / belgedeki tüm tema isabetleri (belge başına hesaplanıp ortalaması alınmıştır). '
         'n: tema isabeti olan belge / dönemdeki belge.\n† İki belgelik dönem; yorumlanmamalıdır. Belge türleri farklı serilerdir; kalın çizgiler türler arası sınırı gösterir.',
         fontsize=6.8, ha='left', va='bottom')
fig.subplots_adjust(left=0.17, right=0.95, top=0.9, bottom=0.25)
fig.savefig(f'{F}/Sekil_5_who_yonetsel_boyutlar.png', dpi=300); fig.savefig(f'{F}/Sekil_5_who_yonetsel_boyutlar.svg')
print('ok')

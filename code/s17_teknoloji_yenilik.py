"""s17 — Teknoloji ve yenilik gündeminin tarihsel izi (makale v6, bölüm 3.6 ve 4.10).

Birim: sağlık cümlesi (en çok 80 kelime; daha uzun 'cümleler' tablo dökümleridir) (s09 çıktısı veri/revizyon/saglik_cumleleri.csv.gz). Yalnızca sağlık cümlelerinde,
dört teknoloji–yenilik kategorisinin geçip geçmediği küçük harfe çevrilmiş cümlede düzenli ifadelerle belirlenir.
  K1 Yerli üretim ve sağlık sanayii   (ilaç/aşı/serum üretimi, sağlık sanayii, yerlileştirme)
  K2 Tıbbi cihaz ve sağlık teknolojisi (tıbbi cihaz, teknoloji, biyoteknoloji, ileri tıbbi donanım)
  K3 Bilgi sistemleri ve dijital sağlık (bilgi sistemi, bilişim, elektronik kayıt, e-sağlık, dijital, tele-)
  K4 Ar-Ge, yenilik ve ticarileştirme   (Ar-Ge, inovasyon, yenilikçi, patent, klinik araştırma, girişimci, teknopark)
Ölçüler
  - Grup düzeyinde: kategori içeren sağlık cümlelerinin yüzdesi (havuz), ilk görüldüğü yıl.
  - Belge düzeyinde: belgedeki sağlık cümlelerinin yüzdesi; yıl ile Spearman ρ (kalkınma planları n = 12;
    Cumhurbaşkanlığı yıllık programları 2019–2026 n = 8; hükümet programları sağlık cümlesi olan tüm programlar),
    son hükümet programları (2002–2016) ile yıllık programlar (2019–2026) için Mann-Whitney U.
    Holm düzeltmesi her test ailesinde 5 ölçüye (K1–K4 ve herhangi biri) uygulanır.
Çıktılar: veri/revizyon/teknoloji_yenilik_gruplar.csv, teknoloji_yenilik_egilim.csv, teknoloji_yenilik_ilk_yil.csv,
          teknoloji_yenilik_belge.csv, teknoloji_yenilik_ornek_cumleler.csv (kategori başına 10 rastgele örnek; ön denetim için)"""
import os, re, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

S = pd.read_csv(f'{RV}/saglik_cumleleri.csv.gz')
n_ = lambda s: s.replace('I', 'ı').replace('İ', 'i').lower().translate(str.maketrans({'â': 'a', 'î': 'i', 'û': 'u'}))
S['n'] = S.Cumle.map(n_)

URUN = r'(?:ilaç|ilac|edviye|aşı|serum|biyolojik ürün|hammadde|etken madde)'
URET = r'(?:üret|imal|sanayi|fabrika|yerli|milli)'
KAT = {
    'K1_Yerli_uretim_ve_saglik_sanayii': [rf'\b{URUN}\w*\b.{{0,60}}\b{URET}', rf'\b{URET}\w*\b.{{0,60}}\b{URUN}',
                                           r'\bsağlık sanayi', r'\byerlileştir', r'\byerli üretim', r'\bmillileştir'],
    'K2_Tibbi_cihaz_ve_saglik_teknolojisi': [r'\btıbbi cihaz', r'\bcihaz', r'\bteknoloji', r'\bbiyoteknoloji', r'\btomograf',
                                             r'\bmanyetik rezonans', r'\btıbbi donanım', r'\bileri tıp', r'\bgenom', r'\bnükleer tıp'],
    'K3_Bilgi_sistemleri_ve_dijital_saglik': [r'\bbilgi sistem', r'\bbilişim', r'\belektronik (?:sağlık|hasta|kayıt|reçete|imza|ortam|tabanlı|başvuru|randevu)', r'\be-sağlık', r'\be-nabız',
                                              r'\bdijital', r'\bveri taban', r'\btele(?:tıp|sağlık|radyoloji)', r'\buzaktan (?:sağlık|tanı|izlem|hizmet)',
                                              r'\byapay zek', r'\bbüyük veri', r'\bmobil sağlık', r'\bsağlık-net\b', r'\bkayıt sistem'],
    'K4_ArGe_yenilik_ve_ticarilestirme': [r'\bar-?ge\b', r'\baraştırma[- ](?:ve )?geliştirme', r'\binovasyon', r'\byenilikçi',
                                          r'\bpatent', r'\bticarileştir', r'\bklinik araştırma', r'\bgirişimci', r'\bteknopark',
                                          r'\bteknoloji transfer', r'\bkuluçka'],
}
KK = list(KAT)
# Sağlık çapası: kategori ifadesinin en çok PENCERE karakter yakınında insan sağlığına özgü bir terim bulunmalıdır.
# 'iş sağlığı', 'hayvan/bitki sağlığı' ve sorumlu kuruluş sütunlarından gelen 'sağlık bakanlığı' çapa sayılmaz.
CAPA = re.compile(r'\bsağlı(?:k|ğ)(?!\w* bakanlığ)|\bsıhh|\btıbb|\btıp\b|\bilaç|\bilac|\bedviye|\başı(?!r)|\bserum|\bhastane|\bhasta\b|\bhastalar|'
                  r'\bhastalık|\bhekim|\bklinik|\btedavi|\btanı\b|\bteşhis|\bteleradyoloji|\be-nabız|\bbiyoteknoloji|\becza|\başılar')
DISLA = re.compile(r'\b(?:iş|hayvan|bitki|veteriner)\w* sağlı')
PENCERE = CFG.get('teknoloji_yenilik', {}).get('pencere', 80)
MAKS_KELIME = CFG.get('teknoloji_yenilik', {}).get('maks_kelime', 80)


TARIM = re.compile(r'\bhayvan|\bveteriner|\bzirai|\bbitki|\bzararlı')
DOKUM = re.compile(r'\.{4,}|(?:\d+, ){2,}\d+|•.*•')       # içindekiler, dizin ve madde imli liste satırları


def isabet(s, rx):
    if len(s.split()) > MAKS_KELIME: return 0          # tablo dökümü niteliğindeki uzun "cümleler"
    if TARIM.search(s) or DOKUM.search(s): return 0
    t = DISLA.sub(' ', s)
    for m in rx.finditer(t):
        a, b = max(0, m.start() - PENCERE), m.end() + PENCERE
        if CAPA.search(t[a:m.start()] + ' ' + t[m.end():b]) or CAPA.match(m.group(0)): return 1
    return 0


for k, pats in KAT.items():
    rx = re.compile('|'.join(pats))
    S[k] = S.n.map(lambda s, rx=rx: isabet(s, rx))
S['Herhangi'] = S[KK].max(axis=1)
MEAS = KK + ['Herhangi']


def grp(r):
    if r.Tur == 'Hükümet programı':
        return '1 HP 1920–1959' if r.Yil < 1960 else ('2 HP 1960–1979' if r.Yil < 1980 else ('3 HP 1980–2001' if r.Yil < 2002 else '4 HP 2002–2016'))
    if r.Tur == 'Kalkınma planı':
        return '5 Plan 1–3 (1963–1977)' if r.Yil < 1979 else ('6 Plan 4–6 (1979–1994)' if r.Yil < 1996 else ('7 Plan 7–9 (1996–2013)' if r.Yil < 2014 else '8 Plan 10–12 (2014–2028)'))
    return '9 Yıllık program 2018–2026'


S['Grup'] = S.apply(grp, axis=1)
G = S.groupby('Grup')
T = pd.DataFrame({'Belge': G.Belge_ID.nunique(), 'Saglik_cumlesi': G.size()})
for m in MEAS: T[m + '_%'] = (G[m].mean() * 100).round(1)
T.to_csv(f'{RV}/teknoloji_yenilik_gruplar.csv', encoding='utf-8-sig')

# ilk görüldüğü yıl (belge türüne göre)
ilk = []
for tur, tt in [('Hükümet programı', ['Hükümet programı']), ('Kalkınma planı', ['Kalkınma planı']),
                ('Yıllık program', ['Yıllık program (Bakanlar Kurulu)', 'Cumhurbaşkanlığı yıllık programı'])]:
    x = S[S.Tur.isin(tt)]
    for m in MEAS:
        y = x[x[m] == 1]
        ilk.append(dict(Belge_turu=tur, Kategori=m, Ilk_yil=int(y.Yil.min()) if len(y) else None,
                        Ilk_belge=y.sort_values('Yil').Belge_ID.iloc[0] if len(y) else None, Cumle_sayisi=int(len(y))))
pd.DataFrame(ilk).to_csv(f'{RV}/teknoloji_yenilik_ilk_yil.csv', index=False, encoding='utf-8-sig')

# belge düzeyi
B = S.groupby(['Belge_ID', 'Tur', 'Yil'])[MEAS].mean().mul(100).reset_index()
B['Saglik_cumlesi'] = S.groupby(['Belge_ID', 'Tur', 'Yil']).size().values
B.to_csv(f'{RV}/teknoloji_yenilik_belge.csv', index=False, encoding='utf-8-sig')


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for i, j in enumerate(o):
        run = max(run, min(1, (m - i) * p[j])); adj[j] = run
    return adj


E = []
aileler = {'Kalkınma planları (yıl, n = 12)': B[B.Tur == 'Kalkınma planı'],
           'Yıllık programlar 2019–2026 (yıl, n = 8)': B[B.Tur == 'Cumhurbaşkanlığı yıllık programı'],
           'Hükümet programları (yıl)': B[B.Tur == 'Hükümet programı']}
for ad, x in aileler.items():
    r = [stats.spearmanr(x.Yil, x[m]) for m in MEAS]
    rho = [float(a.statistic) if np.isfinite(a.statistic) else np.nan for a in r]
    p = [float(a.pvalue) if np.isfinite(a.pvalue) else 1.0 for a in r]
    for m, a, b, c in zip(MEAS, rho, p, holm(p)):
        E.append(dict(Aile=ad, n=len(x), Olcu=m, Test='Spearman', Istatistik=round(a, 3) if np.isfinite(a) else None, p=round(b, 4), p_Holm=round(c, 4)))
hp = B[(B.Tur == 'Hükümet programı') & (B.Yil >= 2002)]; yp = B[B.Tur == 'Cumhurbaşkanlığı yıllık programı']
r = [stats.mannwhitneyu(hp[m], yp[m], alternative='two-sided') for m in MEAS]
p = [float(a.pvalue) for a in r]
for m, a, b, c in zip(MEAS, r, p, holm(p)):
    E.append(dict(Aile=f'HP 2002–2016 (n = {len(hp)}) – YP 2019–2026 (n = {len(yp)})', n=len(hp) + len(yp), Olcu=m, Test='Mann-Whitney U',
                  Istatistik=float(a.statistic), p=round(b, 4), p_Holm=round(c, 4),
                  Ortalama_HP=round(hp[m].mean(), 1), Ortalama_YP=round(yp[m].mean(), 1)))
pd.DataFrame(E).to_csv(f'{RV}/teknoloji_yenilik_egilim.csv', index=False, encoding='utf-8-sig')

# ön denetim için örnek cümleler (kategori başına 10; seed sabit)
rs = np.random.RandomState(CFG['seeds']['revizyon'])
orn = []
for m in KK:
    y = S[S[m] == 1]
    for _, q in y.sample(min(10, len(y)), random_state=rs).iterrows():
        orn.append(dict(Kategori=m, Belge_ID=q.Belge_ID, Yil=q.Yil, Cumle=q.Cumle))
pd.DataFrame(orn).to_csv(f'{RV}/teknoloji_yenilik_ornek_cumleler.csv', index=False, encoding='utf-8-sig')

print(T.to_string()); print(pd.DataFrame(ilk).to_string()); print(pd.DataFrame(E).to_string())

# ---- Şekil 6: belge türüne göre dört kategorinin seyri (küçük çoklu paneller; s08 ile aynı görsel stil)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
os.makedirs(FIG, exist_ok=True)
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
                     'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.titlesize': 9, 'axes.titleweight': 'bold',
                     'axes.titlecolor': INK, 'axes.titlelocation': 'left', 'legend.frameon': False})
TURLER = [('Hükümet programı', ['Hükümet programı'], BLUE, 'o'),
          ('Kalkınma planı', ['Kalkınma planı'], ORANGE, 's'),
          ('Yıllık program', ['Yıllık program (Bakanlar Kurulu)', 'Cumhurbaşkanlığı yıllık programı'], AQUA, '^')]
BASLIK = {'K1_Yerli_uretim_ve_saglik_sanayii': 'Yerli üretim ve sağlık sanayii',
          'K2_Tibbi_cihaz_ve_saglik_teknolojisi': 'Tıbbi cihaz ve sağlık teknolojisi',
          'K3_Bilgi_sistemleri_ve_dijital_saglik': 'Bilgi sistemleri ve dijital sağlık',
          'K4_ArGe_yenilik_ve_ticarilestirme': 'Ar-Ge, yenilik ve ticarileştirme'}
fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.2), sharex=True)
for ax, k in zip(axs.flat, KK):
    for ad, tt, c, mk in TURLER:
        x = B[B.Tur.isin(tt) & (B.Saglik_cumlesi >= 3)].sort_values('Yil')
        ax.scatter(x.Yil, x[k], s=22 if mk != 'o' else 14, color=c, marker=mk, edgecolor='white', linewidth=0.6, label=ad, zorder=3)
        if ad != 'Hükümet programı': ax.plot(x.Yil, x[k], color=c, linewidth=1.2, alpha=0.8, zorder=2)
    ax.set_title(BASLIK[k]); ax.set_xlim(1918, 2030); ax.set_ylim(bottom=0)
    ax.set_ylabel('Sağlık cümlelerinin %’si' if ax in axs[:, 0] else '')
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.02), fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1))
for ext in ('png', 'svg'): fig.savefig(f'{FIG}/Sekil_6_teknoloji_yenilik.{ext}', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)

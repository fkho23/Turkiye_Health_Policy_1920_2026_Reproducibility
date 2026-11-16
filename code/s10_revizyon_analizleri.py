"""s10 — Özgün: 10_revizyon_analizleri.py (yollar ve seed/tekrar sayısı kaynağı değişti; değerler aynı).
10_revizyon_analizleri.py — Majör revizyon (16.11.2026) analizleri.
Girdi: 09_cumle_veri_seti.py çıktıları (veri/revizyon/) + 02/05/06 kodlarının ürettiği veri dosyaları.
1) Denetim: korpus sayıları, Kruskal-Wallis ve epsilon-kare, Tablo 5'in doğru örneklemlerle yeniden hesaplanması
2) Program–plan karşılaştırması: plan düzeyinde (bağımsız birim) Wilcoxon + orijinal 34 eşleşme
3) Tema dağılımı HP 2002–2016 vs CB YP 2019–2026: isabet düzeyi ki-kare doğrulaması + belge düzeyi kesin permütasyon
4) 14 tema-yıl eğilimi: doğru Holm, uzunluk denetimli kısmi Spearman, belge içi tema payı eğilimi
5) Kesintili denge: L-basıklık, normal dağılım altında Monte Carlo p, erken dönem dışlamalı varyantlar
6) WHO altı yapı taşı: tekil birincil boyut (ana analiz), alternatif eşleştirme ve cümle düzeyi çoklu kodlama (sağlamlık)
7) Yalnızca sağlık cümlelerinde dönemlerin ayırt edici terimleri (log-likelihood)
Rastgelelik içeren adımlarda tohum sabittir (2026)."""
import os, re, json, math, itertools, collections
import numpy as np, pandas as pd
from scipy import stats

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
O = RV
import sozlukler as _soz; ns = dict(vars(_soz))
TLABEL = ns['TLABEL']; TK = list(TLABEL); norm = ns['norm']
D = pd.read_csv(f'{O}/belge_envanteri.csv'); S = pd.read_csv(f'{O}/saglik_cumleleri.csv.gz')
H = pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv').sort_values(['Yil', 'Hukumet_ID']).reset_index(drop=True)
OUT = {}; rng = np.random.default_rng(seed('revizyon'))
ORDER = ['1920-1923 Meclis Hükümetleri', '1923-1946 Tek Parti', '1946-1960 Çok Partili Dönem', '1960-1980 Planlı Dönem',
         '1980-2002 Neoliberal Dönüşüm', '2002-2018 AK Parti Dönemi']


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1, run)
    return adj


# ---------- 1. denetim ----------
OUT['korpus'] = {t: {'belge': int(len(g)), 'kelime': int(g.Toplam_Kelime.sum()), 'saglik_cumlesi': int(g.Saglik_Cumle_Sayisi.sum())}
                 for t, g in D.groupby('Tur')}
OUT['korpus']['TOPLAM'] = {'belge': int(len(D)), 'kelime': int(D.Toplam_Kelime.sum()), 'saglik_cumlesi': int(D.Saglik_Cumle_Sayisi.sum())}
P0 = pd.read_csv(PARAS)
OUT['korpus']['HP_ham_cikarim_Kelime_sutunu'] = int(P0.Kelime.sum())


def kw(df, col, minn):
    g = [x[col].values for _, x in df.groupby('Donem') if len(x) >= minn]
    n = sum(len(x) for x in g); h, p = stats.kruskal(*g)
    return {'H': round(float(h), 3), 'p': round(float(p), 4), 'epsilon2': round(float(h / (n - 1)), 3), 'n': int(n), 'grup': len(g)}


T5 = []
for lab, df, minn in [('Tüm programlar, altı dönem', H, 1),
                      ('Meclis Hükümetleri hariç, beş dönem', H[~H.Hukumet_ID.str.contains('IVH')], 1),
                      ('500 kelime ve üstü, n ≥ 3 olan dönemler', H[H.Toplam_Kelime >= 500], 3)]:
    r = {'Alt_orneklem': lab}
    for col, c in [('Saglik_Payi_%', 'Cumle'), ('Saglik_Paragraf_Payi_%', 'Paragraf'), ('Saglik_Terim_1000', 'Terim1000')]:
        k = kw(df, col, minn)
        r[f'KW_{c}_H'] = k['H']; r[f'KW_{c}_p'] = k['p']; r[f'KW_{c}_eps2'] = k['epsilon2']; r['n'] = k['n']; r['grup'] = k['grup']
    keep = [d for d, x in df.groupby('Donem') if len(x) >= minn]
    sub = df[df.Donem.isin(keep)]
    s = stats.spearmanr(sub.Yil, sub['Saglik_Payi_%'])
    r['Spearman_rho'] = round(float(s.statistic), 3); r['Spearman_p'] = round(float(s.pvalue), 4)
    T5.append(r)
T5 = pd.DataFrame(T5); T5.to_csv(f'{O}/tablo5_duzeltilmis.csv', index=False, encoding='utf-8-sig'); OUT['tablo5'] = T5.to_dict('records')
OUT['epsilon2_formulu'] = 'epsilon^2 = H / (n - 1); H/((n^2-1)/(n+1)) ile özdeştir'

# ---------- 2. program–plan ----------
E = pd.read_csv(f'{V}/program_plan_eslestirme.csv')
w = stats.wilcoxon(E.Program_Pay, E.Plan_Pay)
OUT['wilcoxon_34_eslesme'] = {'W': float(w.statistic), 'p': round(float(w.pvalue), 4), 'n': len(E),
                             'program_altinda': int((E.Program_Pay < E.Plan_Pay).sum())}
PL = E.groupby('Plan').agg(Eslesen_program=('Hukumet_ID', 'size'), Program_medyan=('Program_Pay', 'median'),
                           Program_min=('Program_Pay', 'min'), Program_max=('Program_Pay', 'max'),
                           Plan_pay=('Plan_Pay', 'first'), Ilk_yil=('Yil', 'min'), Son_yil=('Yil', 'max')).reset_index()
PL['Fark_program_eksi_plan'] = (PL.Program_medyan - PL.Plan_pay)
PL = PL.round(2); PL.to_csv(f'{O}/plan_duzeyi_karsilastirma.csv', index=False, encoding='utf-8-sig')
wp = stats.wilcoxon(PL.Program_medyan, PL.Plan_pay)
b = [np.median(rng.choice(PL.Fark_program_eksi_plan.values, len(PL))) for _ in range(CFG['bootstrap_plan_farki'])]
OUT['wilcoxon_plan_duzeyi'] = {'n_plan': len(PL), 'W': float(wp.statistic), 'p_kesin': round(float(wp.pvalue), 4),
                               'program_altinda': int((PL.Fark_program_eksi_plan < 0).sum()),
                               'medyan_fark': round(float(PL.Fark_program_eksi_plan.median()), 2),
                               'medyan_fark_GA95_bootstrap': [round(float(np.percentile(b, 2.5)), 2), round(float(np.percentile(b, 97.5)), 2)],
                               'farklar_plan_1_6': PL[PL.Plan <= 'DEVPLAN-06'].Fark_program_eksi_plan.tolist(),
                               'farklar_plan_7_10': PL[PL.Plan >= 'DEVPLAN-07'].Fark_program_eksi_plan.tolist()}

# ---------- 3. tema dağılımı HP 2002–2016 vs CB YP 2019–2026 ----------
S['grp'] = np.where((S.Tur == 'Hükümet programı') & (S.Yil >= 2002), 'HP',
                    np.where(S.Tur == 'Cumhurbaşkanlığı yıllık programı', 'YP', ''))
DT = S.groupby('Belge_ID')[TK].sum(); DT['grp'] = S.groupby('Belge_ID').grp.first()
ct = np.vstack([DT[DT.grp == 'HP'][TK].sum().values, DT[DT.grp == 'YP'][TK].sum().values])
chi = stats.chi2_contingency(ct); N = ct.sum()
OUT['tema_kikare_isabet'] = {'chi2': round(float(chi[0]), 1), 'df': int(chi[2]), 'p': float(chi[1]), 'N_isabet': int(N),
                            'CramerV': round(float(math.sqrt(chi[0] / N)), 3), 'beklenen_<5_hucre': int((chi[3] < 5).sum()),
                            'beklenen_min': round(float(chi[3].min()), 2), 'HP_isabet': int(ct[0].sum()), 'YP_isabet': int(ct[1].sum())}
G = DT[DT.grp.isin(['HP', 'YP'])].copy(); OUT['tema_isabetsiz_belge_dislandi'] = G[G[TK].sum(axis=1) == 0].index.tolist(); G = G[G[TK].sum(axis=1) > 0]
prof = G[TK].div(G[TK].sum(axis=1), axis=0).values; lab = (G.grp == 'HP').values


def perm_exact(prof, lab):
    def st(l): return np.abs(prof[l].mean(0) - prof[~l].mean(0)).sum()
    obs = st(lab); cnt = tot = 0
    for comb in itertools.combinations(range(len(lab)), int(lab.sum())):
        l = np.zeros(len(lab), bool); l[list(comb)] = True; tot += 1; cnt += st(l) >= obs - 1e-12
    return obs, cnt / tot, tot


obs, pp, tot = perm_exact(prof, lab)
mHP = prof[lab].mean(0) * 100; mYP = prof[~lab].mean(0) * 100
OUT['tema_belge_duzeyi_permutasyon'] = {'istatistik': 'Σ|belge ortalaması tema payı farkı|', 'gozlenen': round(float(obs), 3),
                                        'p_kesin': round(pp, 4), 'permutasyon': tot, 'n_HP': int(lab.sum()), 'n_YP': int((~lab).sum()),
                                        'sira_kor_belge_ort': round(float(stats.spearmanr(mHP, mYP).statistic), 3),
                                        'sira_kor_belge_ort_p': round(float(stats.spearmanr(mHP, mYP).pvalue), 4)}
pd.DataFrame({'Tema': [TLABEL[k] for k in TK], 'HP_2002_2016_belge_ort_%': mHP.round(1), 'YP_2019_2026_belge_ort_%': mYP.round(1),
              'HP_havuz_%': (ct[0] / ct[0].sum() * 100).round(1), 'YP_havuz_%': (ct[1] / ct[1].sum() * 100).round(1),
              'HP_isabet': ct[0], 'HP_beklenen': chi[3][0].round(1)}).to_csv(f'{O}/tema_dagilimi_belge_duzeyi.csv', index=False, encoding='utf-8-sig')

# ---------- 4. 14 tema eğilimi ----------
T = pd.read_csv(f'{V}/tema_varlik_matrisi.csv').merge(H[['Hukumet_ID', 'Toplam_Kelime']], on='Hukumet_ID')
lg = np.log(T.Toplam_Kelime.values)


def partial_spearman(x, y, z):
    rx, ry, rz = [stats.rankdata(v) for v in (x, y, z)]
    ex = rx - np.polyval(np.polyfit(rz, rx, 1), rz); ey = ry - np.polyval(np.polyfit(rz, ry, 1), rz)
    r = np.corrcoef(ex, ey)[0, 1]; n = len(x); t = r * math.sqrt((n - 3) / (1 - r * r))
    return float(r), float(2 * stats.t.sf(abs(t), n - 3))


HT2 = H[H[TK].sum(axis=1) > 0]
rows = []
for k in TK:
    s = stats.spearmanr(T.Yil, T[k]); pr, ppv = partial_spearman(T.Yil.values, T[k].values, lg)
    sh = HT2[k] / HT2[TK].sum(axis=1); s2 = stats.spearmanr(HT2.Yil, sh)
    rows.append(dict(Tema=TLABEL[k], n=len(T), Varlik_orani_tum=round(T[k].mean() * 100, 1), rho=round(float(s.statistic), 3), p=float(s.pvalue),
                     kismi_rho_uzunluk=round(pr, 3), kismi_p=ppv, n_pay=len(HT2), pay_rho=round(float(s2.statistic), 3), pay_p=float(s2.pvalue),
                     uzunluk_varlik_rho=round(float(stats.spearmanr(lg, T[k]).statistic), 3)))
TT = pd.DataFrame(rows)
TT['p_Holm'] = holm(TT.p); TT['kismi_p_Holm'] = holm(TT.kismi_p); TT['pay_p_Holm'] = holm(TT.pay_p)
TT['Yon'] = np.where(TT.p_Holm < 0.05, np.where(TT.rho > 0, 'Artış', 'Azalış'), 'Anlamlı eğilim yok')
for c in ['p', 'kismi_p', 'pay_p', 'p_Holm', 'kismi_p_Holm', 'pay_p_Holm']: TT[c] = TT[c].round(4)
TT = TT.sort_values('p'); TT.to_csv(f'{O}/tema_egilim_holm_uzunluk.csv', index=False, encoding='utf-8-sig')
OUT['tema_holm'] = {'varlik_anlamli': TT[TT.p_Holm < 0.05].Tema.tolist(), 'kismi_anlamli': TT[TT.kismi_p_Holm < 0.05].Tema.tolist(),
                    'pay_anlamli': TT[TT.pay_p_Holm < 0.05].Tema.tolist()}

# ---------- 5. L-basıklık ----------
def lk(x):
    x = np.sort(np.asarray(x, float)); n = len(x); i = np.arange(1, n + 1)
    b0 = x.mean(); b1 = np.sum((i - 1) / (n - 1) * x) / n; b2 = np.sum((i - 1) * (i - 2) / ((n - 1) * (n - 2)) * x) / n
    b3 = np.sum((i - 1) * (i - 2) * (i - 3) / ((n - 1) * (n - 2) * (n - 3)) * x) / n
    return (20 * b3 - 30 * b2 + 12 * b1 - b0) / (2 * b1 - b0)


null = {}


def mc_p(v, n):
    if n not in null: null[n] = np.array([lk(rng.standard_normal(n)) for _ in range(CFG['monte_carlo_l_basiklik'])])
    return (np.sum(null[n] >= v) + 1) / (len(null[n]) + 1)


LKr = []
for lab_, df in [('Tüm seri', H), ('1920 (I. İVH) ve 1925 (4. Hük.) hariç', H[~H.Hukumet_ID.isin(['GOV-1920-IVH1', 'GOV-1925-04'])]),
                 ('500 kelime ve üstü', H[H.Toplam_Kelime >= 500]), ('1946 sonrası', H[H.Yil >= 1946]),
                 ('1923–1945', H[(H.Yil >= 1923) & (H.Yil < 1946)])]:
    d = np.diff(df['Saglik_Payi_%'].values); v = lk(d)
    LKr.append(dict(Seri=lab_, n_degisim=len(d), L_basiklik=round(float(v), 3), MC_p_normal=round(float(mc_p(v, len(d))), 4),
                    Klasik_basiklik_fazlasi=round(float(stats.kurtosis(d)), 2),
                    DAgostino_p_klasik=round(float(stats.kurtosistest(d).pvalue), 4) if len(d) >= 20 else None,
                    En_buyuk_mutlak_degisim=round(float(np.abs(d).max()), 2)))
pd.DataFrame(LKr).to_csv(f'{O}/l_basiklik.csv', index=False, encoding='utf-8-sig'); OUT['l_basiklik'] = LKr
OUT['L_basiklik_normal_referans'] = round(float(np.mean(null[62])), 4)
dd = H[['Hukumet_ID', 'Yil', 'Saglik_Payi_%']].copy(); dd['degisim'] = dd['Saglik_Payi_%'].diff()
OUT['en_buyuk_6_degisim'] = dd.reindex(dd.degisim.abs().sort_values(ascending=False).index).head(6).to_dict('records')

# ---------- 6. WHO altı yapı taşı ----------
DIM = ['HS', 'IG', 'BS', 'TU', 'FN', 'YO']
DLAB = {'HS': 'Hizmet sunumu', 'IG': 'Sağlık insan gücü', 'BS': 'Sağlık bilgi sistemleri', 'TU': 'Tıbbi ürünler ve teknoloji',
        'FN': 'Sağlık finansmanı', 'YO': 'Liderlik ve yönetişim'}
MAP = {'T01_Bulasici_hastalik_ve_koruyucu_saglik': ('HS', ['TU']), 'T02_Tedavi_hizmetleri_ve_hastaneler': ('HS', ['YO']),
       'T03_Saglik_insan_gucu': ('IG', []), 'T04_Birinci_basamak_sosyallestirme_kirsal': ('HS', ['YO']),
       'T05_Finansman_ve_saglik_sigortasi': ('FN', ['YO']), 'T06_Ozel_sektor_ve_piyasa': ('YO', ['FN', 'HS']),
       'T07_Ilac_saglik_sanayii_teknoloji': ('TU', []), 'T08_Ana_cocuk_sagligi_ve_nufus': ('HS', []),
       'T09_Sosyal_yardim_ve_dezavantajli_gruplar': ('HS', ['FN', 'YO']), 'T10_Reform_yonetisim_kalite': ('YO', ['HS']),
       'T11_Dijital_saglik_ve_bilgi_sistemleri': ('BS', ['TU']), 'T12_Saglik_turizmi': ('HS', ['YO']),
       'T13_Saglikli_yasam_ve_kronik_hastaliklar': ('HS', []), 'T14_Acil_afet_ve_ambulans': ('HS', ['YO'])}
pd.DataFrame([(TLABEL[k], DLAB[v[0]], ', '.join(DLAB[x] for x in v[1]) or '—') for k, v in MAP.items()],
             columns=['Tema', 'Birincil_boyut', 'Ikincil_boyut']).to_csv(f'{O}/who_eslestirme_matrisi.csv', index=False, encoding='utf-8-sig')


def dimscores(Sx, mp):
    for d in DIM: Sx[f'P_{d}'] = sum(Sx[k] for k, v in mp.items() if v[0] == d)
    for d in DIM: Sx[f'M_{d}'] = (sum(Sx[k] for k, v in mp.items() if v[0] == d or d in v[1]) > 0).astype(int)
    return Sx


S = dimscores(S, MAP); g = S.groupby('Belge_ID'); B = D.set_index('Belge_ID').copy()
B['Tema_isabet'] = g[TK].sum().sum(axis=1); B['Tema_isabet'] = B.Tema_isabet.fillna(0)
for d in DIM:
    B[f'isabet_{d}'] = g[f'P_{d}'].sum(); B[f'isabet_{d}'] = B[f'isabet_{d}'].fillna(0)
    B[f'pay_{d}'] = B[f'isabet_{d}'] / B.Tema_isabet.replace(0, np.nan) * 100
    B[f'var_{d}'] = (B[f'isabet_{d}'] > 0).astype(int)
    B[f'bin_{d}'] = B[f'isabet_{d}'] / B.Saglik_Cumle_Kelime.replace(0, np.nan) * 1000
    B[f'coklu_{d}'] = g[f'M_{d}'].mean() * 100
MAP2 = dict(MAP); MAP2['T09_Sosyal_yardim_ve_dezavantajli_gruplar'] = ('FN', ['HS', 'YO'])
S2 = dimscores(S.copy(), MAP2); g2 = S2.groupby('Belge_ID')
for d in DIM: B[f'alt_pay_{d}'] = g2[f'P_{d}'].sum() / B.Tema_isabet.replace(0, np.nan) * 100


def grp(row):
    if row.Tur == 'Hükümet programı': return row.Donem
    if row.Tur == 'Kalkınma planı':
        n = int(row.name.split('-')[1])
        return ('Planlar 1–3 (1963–1977)' if n <= 3 else 'Planlar 4–6 (1979–1994)' if n <= 6
                else 'Planlar 7–9 (1996–2013)' if n <= 9 else 'Planlar 10–12 (2014–2028)')
    return 'Yıllık program 2018 (BK)' if row.Tur.startswith('Yıllık') else 'CB yıllık programları 2019–2026'


B['Grup'] = B.apply(grp, axis=1)
GORDER = ORDER + ['Planlar 1–3 (1963–1977)', 'Planlar 4–6 (1979–1994)', 'Planlar 7–9 (1996–2013)', 'Planlar 10–12 (2014–2028)',
                  'Yıllık program 2018 (BK)', 'CB yıllık programları 2019–2026']
B.reset_index().to_csv(f'{O}/belge_duzeyi_who_boyutlari.csv', index=False, encoding='utf-8-sig')
rows = []
for gname in GORDER:
    x = B[B.Grup == gname]; xh = x[x.Tema_isabet > 0]
    r = {'Grup': gname, 'Belge': len(x), 'Tema_isabeti_olan_belge': len(xh), 'Toplam_isabet': int(x.Tema_isabet.sum())}
    for d in DIM:
        L = DLAB[d]
        r[f'{L} | belge ort. pay %'] = round(xh[f'pay_{d}'].mean(), 1) if len(xh) else np.nan
        r[f'{L} | havuz pay %'] = round(x[f'isabet_{d}'].sum() / x.Tema_isabet.sum() * 100, 1) if x.Tema_isabet.sum() else np.nan
        r[f'{L} | içeren belge'] = int(x[f'var_{d}'].sum()); r[f'{L} | içeren belge %'] = round(x[f'var_{d}'].mean() * 100, 1)
        r[f'{L} | medyan/1000 sağlık kelimesi'] = round(xh[f'bin_{d}'].median(), 2) if len(xh) else np.nan
        r[f'{L} | çoklu kodlama: sağlık cümlesi %'] = round(xh[f'coklu_{d}'].mean(), 1) if len(xh) else np.nan
        r[f'{L} | alternatif eşleştirme belge ort. %'] = round(xh[f'alt_pay_{d}'].mean(), 1) if len(xh) else np.nan
    rows.append(r)
W = pd.DataFrame(rows); W.to_csv(f'{O}/who_boyut_donem_tablosu.csv', index=False, encoding='utf-8-sig')
tr = []
for lab_, x in [('Hükümet programları 1920–2016', B[(B.Tur == 'Hükümet programı') & (B.Tema_isabet > 0)]),
                ('Kalkınma planları 1963–2028', B[B.Tur == 'Kalkınma planı']),
                ('CB yıllık programları 2019–2026', B[B.Tur == 'Cumhurbaşkanlığı yıllık programı'])]:
    rr = []
    for d in DIM:
        s = stats.spearmanr(x.Yil, x[f'pay_{d}']); rr.append(dict(Seri=lab_, Boyut=DLAB[d], n=len(x), rho=round(float(s.statistic), 3), p=float(s.pvalue)))
    for r_, a in zip(rr, holm([r_['p'] for r_ in rr])):
        r_['p_Holm'] = round(float(a), 4); r_['p'] = round(r_['p'], 4); tr.append(r_)
    # sağlamlık: çoklu kodlama ve alternatif eşleştirme eğilimleri
    for d in DIM:
        s = stats.spearmanr(x.Yil, x[f'coklu_{d}']); s3 = stats.spearmanr(x.Yil, x[f'alt_pay_{d}'])
        OUT.setdefault('who_egilim_saglamlik', []).append(dict(Seri=lab_, Boyut=DLAB[d], coklu_rho=round(float(s.statistic), 3), coklu_p=round(float(s.pvalue), 4),
                                                                alt_rho=round(float(s3.statistic), 3), alt_p=round(float(s3.pvalue), 4)))
TR = pd.DataFrame(tr); TR.to_csv(f'{O}/who_boyut_egilim.csv', index=False, encoding='utf-8-sig'); OUT['who_egilim'] = tr
G2 = B[(((B.Tur == 'Hükümet programı') & (B.Yil >= 2002)) | (B.Tur == 'Cumhurbaşkanlığı yıllık programı')) & (B.Tema_isabet > 0)]
l2 = (G2.Tur == 'Hükümet programı').values
o2, p2, t2 = perm_exact(G2[[f'pay_{d}' for d in DIM]].values / 100, l2)
mw = [stats.mannwhitneyu(G2[l2][f'pay_{d}'], G2[~l2][f'pay_{d}']).pvalue for d in DIM]
OUT['who_HP_vs_YP'] = {'gozlenen': round(float(o2), 3), 'p_kesin': round(p2, 4), 'perm': t2,
                       'boyut_MW_p': {DLAB[d]: round(float(x), 4) for d, x in zip(DIM, mw)},
                       'boyut_MW_p_Holm': {DLAB[d]: round(float(x), 4) for d, x in zip(DIM, holm(mw))},
                       'HP_ort': {DLAB[d]: round(float(G2[l2][f'pay_{d}'].mean()), 1) for d in DIM},
                       'YP_ort': {DLAB[d]: round(float(G2[~l2][f'pay_{d}'].mean()), 1) for d in DIM}}
HPB = B[B.Tur == 'Hükümet programı']
OUT['who_varlik_uzunluk_rho'] = {DLAB[d]: round(float(stats.spearmanr(np.log(HPB.Toplam_Kelime), HPB[f'var_{d}']).statistic), 3) for d in DIM}

# ---------- 7. sağlık cümlelerinde ayırt edici terimler ----------
STOP = set(norm(w) for w in '''ve ile bir bu da de için olan olarak daha çok en gibi kadar her şekilde ise ya veya ki ne o şu bunu bunun buna bunlar bütün tüm hem ancak fakat yani yeni ayrıca olacak edilecek edilmesi edilmiştir edecek etmek olmak olduğu olduğunu olunacak olmuştur yapılacak sağlanacak bulunan bulunmaktadır kendi gerek gereken hususunda hususu hususta ait dair göre karşı arasında üzerinde önemli büyük memleket memleketimiz memleketimizin hükümet hükümetimiz hükümetimizin milletimizin milli devlet vatandaş vatandaşlarımızın sayın arkadaşlar efendiler cumhuriyet suretle surette lazım lüzumlu icap mevcut tedbir tedbirler gayret gayretle devam alınacak çalışmalar faaliyet hizmet hizmetleri hizmetlerinin sahasında alanında alanında önem verilecek getirilecek yıl yılında yılı'''.split())
HS_ = S[S.Tur == 'Hükümet programı']
cnt = collections.defaultdict(collections.Counter); forms = collections.defaultdict(collections.Counter)
for d_, txt in zip(HS_.Donem, HS_.Cumle.map(norm)):
    for w_ in re.findall(r"[a-zçğıöşü]+", txt):
        if len(w_) > 2 and w_ not in STOP: cnt[d_][w_[:6]] += 1; forms[w_[:6]][w_] += 1
tot = collections.Counter()
for c in cnt.values(): tot.update(c)
NN = sum(tot.values()); rows = []
for d_ in ORDER:
    at = sum(cnt[d_].values()); bt = NN - at
    for s_, a in cnt[d_].items():
        if a < 4: continue
        b_ = tot[s_] - a; E1 = at * (a + b_) / NN; E2 = bt * (a + b_) / NN
        ll = 2 * (a * math.log(a / E1) + (b_ * math.log(b_ / E2) if b_ else 0))
        if a / at > b_ / max(bt, 1) and ll > 10.83:
            rows.append(dict(Donem=d_, Kok=s_, Ornek_bicim=forms[s_].most_common(1)[0][0],
                             Bicimler='; '.join(f for f, _ in forms[s_].most_common(4)), Frekans=a, LL=round(ll, 1)))
LL = pd.DataFrame(rows).sort_values(['Donem', 'LL'], ascending=[True, False])
LL.to_csv(f'{O}/saglik_cumleleri_ayirt_edici_terimler.csv', index=False, encoding='utf-8-sig')
OUT['saglik_LL_ilk8'] = {d_: LL[LL.Donem == d_].head(8)[['Ornek_bicim', 'Bicimler', 'LL']].values.tolist() for d_ in ORDER}
json.dump(OUT, open(f'{O}/revizyon_testleri.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)

pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(T5.to_string()); print(PL.to_string())
print(json.dumps({k: OUT[k] for k in ['korpus', 'wilcoxon_34_eslesme', 'wilcoxon_plan_duzeyi', 'tema_kikare_isabet',
                                      'tema_belge_duzeyi_permutasyon', 'tema_holm', 'who_HP_vs_YP', 'who_varlik_uzunluk_rho',
                                      'L_basiklik_normal_referans']}, ensure_ascii=False, indent=0))
print(TT.to_string()); print(pd.DataFrame(LKr).to_string())
print(W[['Grup', 'Belge', 'Tema_isabeti_olan_belge'] + [f'{DLAB[d]} | belge ort. pay %' for d in DIM]].to_string())
print(TR.to_string()); print(OUT['saglik_LL_ilk8'])

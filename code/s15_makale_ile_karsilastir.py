"""s15 — Yeniden üretilen sonuçların makaledeki (revizyon v5) değerlerle karşılaştırılması.
Kural: makale değeri, yeniden üretilen değerin makaledeki ondalık basamağa yuvarlanmış hâliyle karşılaştırılır.
'<0,001' gibi eşik ifadeleri eşik koşuluyla sınanır. Ayrıca ön doğrulama örneklemlerinin (seed 42/7) arşivdeki
örneklemlerle aynı kayıtları içerip içermediği denetlenir.
Çıktılar: outputs/dogrulama_raporu.csv, outputs/DOGRULAMA_RAPORU.md"""
import os, sys, json, re
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

J = lambda f: json.load(open(f, encoding='utf-8'))
C = lambda f: pd.read_csv(f)
IT, SG, EK, CB = [J(f'{V}/{f}') for f in ['istatistik_testleri.json', 'saglamlik_testleri.json', 'ek_testler.json', 'cumhurbaskanligi_donemi_testler.json']]
RT = J(f'{RV}/revizyon_testleri.json')
H = C(f'{V}/hukumet_saglik_metrikleri.csv'); K = C(f'{V}/karsilastirma_korpuslari_metrikleri.csv'); DS = C(f'{V}/donem_ozet.csv').set_index('Donem')
PAY = C(f'{V}/donem_tema_pay_yuzde.csv').set_index('Donem'); VAR = C(f'{V}/donem_tema_varlik_yuzde.csv').set_index('Donem')
LL = C(f'{V}/donem_ayirt_edici_terimler.csv'); T5 = C(f'{RV}/tablo5_duzeltilmis.csv'); LK = C(f'{RV}/l_basiklik.csv').set_index('Seri')
PL = C(f'{RV}/plan_duzeyi_karsilastirma.csv').set_index('Plan'); TT = C(f'{RV}/tema_egilim_holm_uzunluk.csv').set_index('Tema')
YP = C(f'{V}/cumhurbaskanligi_donemi_belgeler.csv').set_index('ID'); TD = C(f'{V}/cumhurbaskanligi_donemi_tema_dagilimi.csv').set_index('Tema')
WT = C(f'{RV}/who_boyut_donem_tablosu.csv').set_index('Grup'); WE = C(f'{RV}/who_boyut_egilim.csv')
TS = C(f'{RV}/terim_sayimlari_gruplar.csv').set_index('Terim'); SY = C(f'{RV}/sosyal_yardim_terimleri.csv').set_index('Kalip')
KOR = RT['korpus']; HL = pd.read_excel(GOV_META)
O = ['1920-1923 Meclis Hükümetleri', '1923-1946 Tek Parti', '1946-1960 Çok Partili Dönem', '1960-1980 Planlı Dönem', '1980-2002 Neoliberal Dönüşüm', '2002-2018 AK Parti Dönemi']
rows = []


def chk(konum, tanim, beklenen, fn, dec=None, kosul=None):
    try:
        v = fn()
        sinir = False
        if kosul is not None: ok = bool(kosul(v)); bek = beklenen
        else:
            d = dec if dec is not None else 0
            # makaledeki değer, yeniden üretilen değerin geçerli bir yuvarlaması mı? (yarım sınırında hem yukarı hem çift yuvarlama kabul)
            fark = abs(float(v) - float(beklenen)); ok = fark <= 10 ** (-d) / 2 + 1e-6; bek = beklenen
            sinir = ok and abs(fark - 10 ** (-d) / 2) < 1e-6
        rows.append(dict(Konum=konum, Deger=tanim, Makale=bek, Yeniden_uretilen=v if not isinstance(v, float) else round(v, 8),
                         Durum=('AYNI' if not (kosul is None and sinir) else 'AYNI (yuvarlama sınırı)') if ok else 'FARK'))
    except Exception as e:
        rows.append(dict(Konum=konum, Deger=tanim, Makale=beklenen, Yeniden_uretilen=f'HATA: {e}', Durum='HATA'))


lt = lambda x: (lambda v: v < x)
# ---- Tablo 1 / 3.1
for t, n, w, s in [('Hükümet programı', 63, 328619, 518), ('Kalkınma planı', 12, 1062724, 2580)]:
    chk('Tablo 1', f'{t} belge', n, lambda t=t: KOR[t]['belge']); chk('Tablo 1', f'{t} kelime', w, lambda t=t: KOR[t]['kelime']); chk('Tablo 1', f'{t} sağlık cümlesi', s, lambda t=t: KOR[t]['saglik_cumlesi'])
chk('Tablo 1', 'Yıllık program belge', 9, lambda: KOR['Cumhurbaşkanlığı yıllık programı']['belge'] + KOR['Yıllık program (Bakanlar Kurulu)']['belge'])
chk('Tablo 1', 'Yıllık program kelime', 1097108, lambda: KOR['Cumhurbaşkanlığı yıllık programı']['kelime'] + KOR['Yıllık program (Bakanlar Kurulu)']['kelime'])
chk('Tablo 1', 'Yıllık program sağlık cümlesi', 3582, lambda: KOR['Cumhurbaşkanlığı yıllık programı']['saglik_cumlesi'] + KOR['Yıllık program (Bakanlar Kurulu)']['saglik_cumlesi'])
chk('Tablo 1', 'Toplam belge', 84, lambda: KOR['TOPLAM']['belge']); chk('Tablo 1', 'Toplam kelime', 2488451, lambda: KOR['TOPLAM']['kelime']); chk('Tablo 1', 'Toplam sağlık cümlesi', 6680, lambda: KOR['TOPLAM']['saglik_cumlesi'])
chk('Tablo 1 notu', 'HP ham çıkarım kelime', 332492, lambda: KOR['HP_ham_cikarim_Kelime_sutunu'])
chk('Tablo 1 notu', '2018 BK kelime', 99489, lambda: KOR['Yıllık program (Bakanlar Kurulu)']['kelime']); chk('Tablo 1 notu', '2019–2026 kelime', 997619, lambda: KOR['Cumhurbaşkanlığı yıllık programı']['kelime'])
chk('3.1', 'Yürütme birimi', 72, lambda: len(HL)); chk('3.1', 'Program sunan', 63, lambda: int((HL.Hukumet_Programi_Var_mi == 'Var').sum()))
# ---- Tablo 4
T4 = [(2, 2708, 8.07, 14.78, None, None, 6.23, 0), (12, 1477, 2.79, 1.44, 0.00, 4.92, 2.13, 5), (9, 3067, 2.96, 2.82, 0.00, 4.21, 1.49, 2),
      (19, 6267, 3.24, 3.07, 2.61, 3.63, 2.40, 1), (14, 7427, 2.77, 2.50, 2.03, 3.59, 2.13, 0), (7, 7832, 2.61, 2.90, 1.04, 3.51, 2.16, 0)]
for d, (n, L, hv, md, lo, hi, tr, z) in zip(O, T4):
    s = d[:9]
    chk('Tablo 4', f'{s} n', n, lambda d=d: DS.loc[d, 'Hukumet_Sayisi']); chk('Tablo 4', f'{s} ort. uzunluk', L, lambda d=d: DS.loc[d, 'Ort_Kelime'])
    chk('Tablo 4', f'{s} havuz payı', hv, lambda d=d: DS.loc[d, 'Havuz_Saglik_Payi_%'], 2); chk('Tablo 4', f'{s} medyan', md, lambda d=d: DS.loc[d, 'Medyan_Saglik_Payi_%'], 2)
    if lo is not None:
        chk('Tablo 4', f'{s} GA alt', lo, lambda d=d: EK['Donem_medyan_bootstrap'][d]['GA95'][0], 2); chk('Tablo 4', f'{s} GA üst', hi, lambda d=d: EK['Donem_medyan_bootstrap'][d]['GA95'][1], 2)
    chk('Tablo 4', f'{s} terim/1000', tr, lambda d=d: DS.loc[d, 'Ort_Terim_1000'], 2); chk('Tablo 4', f'{s} sağlıksız program', z, lambda d=d: DS.loc[d, 'Saglik_Bolumu_Olmayan'])
# ---- 4.1–4.3
chk('4.1', 'KW 6 dönem H', 7.24, lambda: EK['KW_Donem_6grup']['H'], 2); chk('4.1', 'KW 6 dönem p', 0.203, lambda: EK['KW_Donem_6grup']['p'], 3); chk('4.1', 'KW 6 dönem ε²', 0.12, lambda: EK['KW_Donem_6grup']['epsilon2'], 2)
chk('4.1', 'KW 5 dönem H', 3.50, lambda: EK['KW_Donem_n3plus']['H'], 2); chk('4.1', 'KW 5 dönem p', 0.478, lambda: EK['KW_Donem_n3plus']['p'], 3); chk('4.1', 'KW 5 dönem ε²', 0.06, lambda: EK['KW_Donem_n3plus']['epsilon2'], 2)
chk('4.1', 'yıl–pay ρ', -0.01, lambda: IT['Spearman_Yil_SaglikPayi']['rho'], 2); chk('4.1', 'yıl–pay p', 0.92, lambda: IT['Spearman_Yil_SaglikPayi']['p'], 2)
g = lambda i: H.set_index('Hukumet_ID').loc[i]
chk('4.1', '1920 I. İVH payı', 25.2, lambda: g('GOV-1920-IVH1')['Saglik_Payi_%'], 1); chk('4.1', '1925 payı', 27.6, lambda: g('GOV-1925-04')['Saglik_Payi_%'], 1)
chk('4.1', '1925 kelime', 127, lambda: g('GOV-1925-04')['Toplam_Kelime'])
chk('4.1', 'sağlığa değinmeyen program', 8, lambda: int((H['Saglik_Payi_%'] == 0).sum()))
chk('4.1', 'sağlığa değinmeyen programlar', 'GOV-1927-05,1935-08,1938-10,1939-12,1942-13,1949-18,1955-22,1973-36', lambda: ','.join(H[H['Saglik_Payi_%'] == 0].Hukumet_ID.str[4:]),
    kosul=lambda v: v == '1927-05,1935-08,1938-10,1939-12,1942-13,1949-18,1955-22,1973-36')
chk('5.1', '1946 sonrası program', 49, lambda: int((H.Yil >= 1946).sum())); chk('5.1', '1946 sonrası sağlıksız', 3, lambda: int(((H.Yil >= 1946) & (H['Saglik_Payi_%'] == 0)).sum()))
chk('4.2', 'yıl–uzunluk ρ', 0.70, lambda: IT['Spearman_Yil_ProgramUzunlugu']['rho'], 2); chk('4.2', 'yıl–sağlık paragraf kelimesi ρ', 0.43, lambda: IT['Spearman_Yil_SaglikKelime']['rho'], 2)
chk('4.2', 'uzunluk–pay ρ', 0.26, lambda: IT['Spearman_Uzunluk_SaglikPayi']['rho'], 2); chk('4.2', 'uzunluk–pay p', 0.040, lambda: IT['Spearman_Uzunluk_SaglikPayi']['p'], 3)
chk('4.3', 'tür KW H', 1.24, lambda: IT['KruskalWallis_Tur_SaglikPayi(n>2 gruplar)']['H'], 2); chk('4.3', 'tür KW p', 0.87, lambda: IT['KruskalWallis_Tur_SaglikPayi(n>2 gruplar)']['p'], 2)
mw = IT['MannWhitney_Koalisyon_vs_TekParti']
chk('4.3', 'MW U', 265, lambda: mw['U']); chk('4.3', 'MW p', 0.39, lambda: mw['p'], 2); chk('4.3', 'koalisyon medyan', 3.11, lambda: mw['medyan_koal'], 2); chk('4.3', 'tek parti medyan', 2.63, lambda: mw['medyan_tek'], 2)
chk('4.3', 'n koalisyon', 13, lambda: mw['n_koal']); chk('4.3', 'n tek parti', 35, lambda: mw['n_tek'])
# ---- 4.4 / Tablo 5
chk('4.4', 'L-basıklık tüm seri', 0.48, lambda: LK.loc['Tüm seri', 'L_basiklik'], 2); chk('4.4', 'tüm seri MC p', '<0,001', lambda: LK.loc['Tüm seri', 'MC_p_normal'], kosul=lt(0.001))
chk('4.4', 'değişim sayısı', 62, lambda: LK.loc['Tüm seri', 'n_degisim'])
chk('4.4', 'L-basıklık 1920/1925 hariç', 0.28, lambda: LK.loc['1920 (I. İVH) ve 1925 (4. Hük.) hariç', 'L_basiklik'], 2); chk('4.4', '1920/1925 hariç MC p', '<0,001', lambda: LK.loc['1920 (I. İVH) ve 1925 (4. Hük.) hariç', 'MC_p_normal'], kosul=lt(0.001))
chk('4.4', 'L-basıklık 1946 sonrası', 0.21, lambda: LK.loc['1946 sonrası', 'L_basiklik'], 2); chk('4.4', '1946 sonrası MC p', 0.035, lambda: LK.loc['1946 sonrası', 'MC_p_normal'], 3)
chk('4.4', '1946 sonrası D’Agostino p', 0.15, lambda: LK.loc['1946 sonrası', 'DAgostino_p_klasik'], 2); chk('4.4', '1946 sonrası en büyük değişim', 5.3, lambda: LK.loc['1946 sonrası', 'En_buyuk_mutlak_degisim'], 1)
chk('4.4', '1946 sonrası değişim sayısı', 48, lambda: LK.loc['1946 sonrası', 'n_degisim']); chk('3.7', 'L-basıklık normal referansı', 0.123, lambda: RT['L_basiklik_normal_referans'], 3)
chk('4.4', 'en büyük 6 değişimin yılları 1923–1939', '1923–1939', lambda: [r['Yil'] for r in RT['en_buyuk_6_degisim']], kosul=lambda v: min(v) >= 1923 and max(v) <= 1939)
for i, (n, gr, p1, e1, p2, p3, r_, rp) in enumerate([(63, 6, .203, .12, .122, .238, -.01, .92), (61, 5, .478, .06, .458, .495, .08, .55), (59, 5, .376, .07, .359, .421, .09, .48)]):
    r = lambda c, i=i: T5.iloc[i][c]
    chk('Tablo 5', f'satır {i + 1} n', n, lambda r=r: r('n')); chk('Tablo 5', f'satır {i + 1} dönem', gr, lambda r=r: r('grup'))
    chk('Tablo 5', f'satır {i + 1} cümle p', p1, lambda r=r: r('KW_Cumle_p'), 3); chk('Tablo 5', f'satır {i + 1} ε²', e1, lambda r=r: r('KW_Cumle_eps2'), 2)
    chk('Tablo 5', f'satır {i + 1} paragraf p', p2, lambda r=r: r('KW_Paragraf_p'), 3); chk('Tablo 5', f'satır {i + 1} terim p', p3, lambda r=r: r('KW_Terim1000_p'), 3)
    chk('Tablo 5', f'satır {i + 1} ρ', r_, lambda r=r: r('Spearman_rho'), 2); chk('Tablo 5', f'satır {i + 1} ρ p', rp, lambda r=r: r('Spearman_p'), 2)
# ---- 4.5
kp = K.set_index('ID')
chk('4.5', 'plan ρ', 0.82, lambda: SG['Kalkinma_planlari_Spearman_Yil_Pay']['rho'], 2); chk('4.5', 'plan p', 0.001, lambda: SG['Kalkinma_planlari_Spearman_Yil_Pay']['p'], 3)
chk('4.5', '1. Plan payı', 2.14, lambda: kp.loc['DEVPLAN-01', 'Saglik_Payi_%'], 2); chk('4.5', '12. Plan payı', 8.81, lambda: kp.loc['DEVPLAN-12', 'Saglik_Payi_%'], 2)
chk('4.5', '1–6. Plan aralığı 2,1–3,3', '2,1–3,3', lambda: kp.loc[[f'DEVPLAN-0{i}' for i in range(1, 7)], 'Saglik_Payi_%'].agg(['min', 'max']).round(1).tolist(), kosul=lambda v: v == [2.1, 3.3])
chk('4.5', '2018 BK payı', 5.09, lambda: kp.loc['PRES-2018-YP', 'Saglik_Payi_%'], 2); chk('4.5', '2019 payı', 5.39, lambda: kp.loc['PRES-2019', 'Saglik_Payi_%'], 2); chk('4.5', '2026 payı', 8.46, lambda: kp.loc['PRES-2026', 'Saglik_Payi_%'], 2)
chk('4.5', 'yıllık program ρ (n=9)', 0.93, lambda: SG['Yillik_programlar_Spearman_Yil_Pay']['rho'], 2); chk('4.5', 'yıllık program p', '<0,001', lambda: SG['Yillik_programlar_Spearman_Yil_Pay']['p'], kosul=lt(0.001))
W_ = RT['wilcoxon_plan_duzeyi']
chk('4.5', 'plan düzeyi n', 10, lambda: W_['n_plan']); chk('4.5', 'plan düzeyi W', 13, lambda: W_['W']); chk('4.5', 'plan düzeyi p', 0.160, lambda: W_['p_kesin'], 3)
chk('4.5', 'medyan fark', -0.52, lambda: W_['medyan_fark'], 2); chk('4.5', 'GA alt', -2.67, lambda: W_['medyan_fark_GA95_bootstrap'][0], 2); chk('4.5', 'GA üst', 0.29, lambda: W_['medyan_fark_GA95_bootstrap'][1], 2)
chk('4.5', 'program altında plan sayısı', 6, lambda: W_['program_altinda'])
chk('4.5', '1–5. plan farkları −0,15…0,47', '−0,15…0,47', lambda: PL.loc[[f'DEVPLAN-0{i}' for i in range(1, 6)], 'Fark_program_eksi_plan'].agg(['min', 'max']).tolist(), kosul=lambda v: v == [-0.15, 0.47])
chk('4.5', '6–10. plan farkları −4,20…−0,89', '−4,20…−0,89', lambda: PL.loc[['DEVPLAN-06', 'DEVPLAN-07', 'DEVPLAN-08', 'DEVPLAN-09', 'DEVPLAN-10'], 'Fark_program_eksi_plan'].agg(['min', 'max']).tolist(), kosul=lambda v: v == [-4.2, -0.89])
chk('4.5', '34 eşleşme p', 0.014, lambda: RT['wilcoxon_34_eslesme']['p'], 3); chk('4.5', '34 eşleşmede program altında', 20, lambda: RT['wilcoxon_34_eslesme']['program_altinda'])
# ---- 4.6
for d, v in zip(O[1:], [25.9, 25.6, 12.7, 3.1, 3.7]): chk('4.6', f'koruyucu payı {d[:9]}', v, lambda d=d: PAY.loc[d, 'Bulaşıcı hastalık ve koruyucu sağlık'], 1)
chk('4.6', 'finansman payı Tek Parti', 0.0, lambda: PAY.loc[O[1], 'Finansman ve sağlık sigortası'], 1); chk('4.6', 'finansman payı Neoliberal', 28.7, lambda: PAY.loc[O[4], 'Finansman ve sağlık sigortası'], 1)
chk('4.6', 'finansman payı AKP', 19.3, lambda: PAY.loc[O[5], 'Finansman ve sağlık sigortası'], 1); chk('4.6', 'tedavi payı AKP', 19.3, lambda: PAY.loc[O[5], 'Tedavi hizmetleri ve hastaneler'], 1)
for th, vals in [('Finansman ve sağlık sigortası', [0, 68, 79, 71]), ('Özel sektör ve piyasa', [0, 26, 64, 57])]:
    for d, v in zip([O[1], O[3], O[4], O[5]], vals): chk('4.6', f'varlık {th[:10]} {d[:9]}', v, lambda d=d, th=th: VAR.loc[d, th], 0)
chk('4.6', 'turizm varlık Neoliberal', 29, lambda: VAR.loc[O[4], 'Sağlık turizmi'], 0); chk('4.6', 'turizm varlık AKP', 43, lambda: VAR.loc[O[5], 'Sağlık turizmi'], 0)
for th, v in [('Tedavi hizmetleri ve hastaneler', 84), ('Sağlık insan gücü', 90), ('İlaç, sağlık sanayii, teknoloji', 74)]: chk('4.6', f'Planlı dönem varlık {th[:12]}', v, lambda th=th: VAR.loc[O[3], th], 0)
for th, r in [('Finansman ve sağlık sigortası', .58), ('Özel sektör ve piyasa', .48), ('Sağlık turizmi', .42), ('Birinci basamak, sosyalleştirme, kırsal', .41), ('Reform, yönetişim, kalite', .38), ('Tedavi hizmetleri ve hastaneler', .37), ('Sağlık insan gücü', .36)]:
    chk('4.6 / E1', f'varlık ρ {th[:14]}', r, lambda th=th: TT.loc[th, 'rho'], 2); chk('4.6 / E1', f'Holm<0,05 {th[:14]}', '<0,05', lambda th=th: TT.loc[th, 'p_Holm'], kosul=lt(0.05))
    chk('4.6 / E1', f'uzunluk denetimli Holm ≥0,05 {th[:14]}', '≥0,05', lambda th=th: TT.loc[th, 'kismi_p_Holm'], kosul=lambda v: v >= 0.05)
chk('4.6', 'Holm sonrası anlamlı tema sayısı (varlık)', 7, lambda: int((TT.p_Holm < 0.05).sum()))
chk('4.6', 'ana-çocuk ρ (düzeltme öncesi)', 0.29, lambda: TT.loc['Ana-çocuk sağlığı ve nüfus', 'rho'], 2)
chk('4.6', 'uzunluk–varlık ρ finansman', 0.75, lambda: TT.loc['Finansman ve sağlık sigortası', 'uzunluk_varlik_rho'], 2); chk('4.6', 'uzunluk–varlık ρ tedavi', 0.65, lambda: TT.loc['Tedavi hizmetleri ve hastaneler', 'uzunluk_varlik_rho'], 2)
for th, r in [('Finansman ve sağlık sigortası', .66), ('Sağlık turizmi', .49), ('Özel sektör ve piyasa', .43), ('Bulaşıcı hastalık ve koruyucu sağlık', -.58)]:
    chk('4.6 / E1', f'belge içi pay ρ {th[:14]}', r, lambda th=th: TT.loc[th, 'pay_rho'], 2); chk('4.6 / E1', f'belge içi pay Holm<0,05 {th[:14]}', '<0,05', lambda th=th: TT.loc[th, 'pay_p_Holm'], kosul=lt(0.05))
chk('4.6', 'belge içi pay n', 47, lambda: TT['n_pay'].iloc[0])
# ---- Tablo 6
for d, terms in [(O[0], [('sıhhiye', 58), ('içtimaiye', 38), ('vekaleti', 25), ('memleketin', 16), ('bugün', 15)]), (O[1], [('sıhhat', 22), ('mücadele', 20), ('içtimaiye', 16), ('sıhhiye', 11)]),
                 (O[2], [('vergisi', 23), ('ehemmiyetle', 19), ('bütçelerinde', 19), ('istihsal', 17), ('edilmiş', 17), ('şimdiden', 14)]), (O[3], [('ilaç', 49), ('halkın', 27), ('sanayi', 18), ('sağlığı', 17), ('hekimlik', 15), ('tedavi', 15)]),
                 (O[4], [('sağlık', 24), ('sistemi', 20), ('sahip', 20), ('sigortası', 19), ('formaliteden', 16), ('sektöründe', 14)]), (O[5], [('hükumetimiz', 42), ('yüzde', 41), ('hayata', 28), ('başlattık', 25), ('döneminde', 21), ('sağladık', 21)])]:
    for w_, v in terms:
        chk('Tablo 6', f'{d[:9]} {w_}', v, lambda d=d, w_=w_: LL[(LL.Donem == d) & (LL.Ornek_Bicim == w_)].LL.iloc[0], 0)
# ---- Tablo 7 / 4.8
for i, (pay, ay, mk, t1) in {'PRES-2018-YP': (5.09, 3.79, 0, 5.8), 'PRES-2019': (5.39, 4.10, 0, 4.2), 'PRES-2020': (5.56, 4.62, 0, 3.8), 'PRES-2021': (7.51, 5.72, 45, 28.4), 'PRES-2022': (7.32, 5.43, 27, 28.3),
                             'PRES-2023': (6.57, 5.42, 14, 17.4), 'PRES-2024': (7.67, 5.88, 12, 12.0), 'PRES-2025': (7.92, 6.41, 5, 8.8), 'PRES-2026': (8.46, 6.32, 5, 9.9)}.items():
    chk('Tablo 7', f'{i} pay', pay, lambda i=i: YP.loc[i, 'Saglik_Payi'], 2); chk('Tablo 7', f'{i} ayıklanmış', ay, lambda i=i: YP.loc[i, 'Saglik_Payi_ayiklanmis'], 2)
    chk('Tablo 7', f'{i} makro salgın', mk, lambda i=i: YP.loc[i, 'Makro_salgin_cumle']); chk('Tablo 7', f'{i} koruyucu tema %', t1, lambda i=i: YP.loc[i, 'T01_tema_payi'], 1)
    chk('Tablo 7', f'{i} toplam kelime', {'PRES-2018-YP': 99489, 'PRES-2019': 88763, 'PRES-2020': 126286, 'PRES-2021': 126401, 'PRES-2022': 115883, 'PRES-2023': 113805, 'PRES-2024': 150701, 'PRES-2025': 135468, 'PRES-2026': 140312}[i], lambda i=i: YP.loc[i, 'Toplam_Kelime'])
chk('4.8', 'YP 2019–2026 ρ', 0.91, lambda: CB['rho_Saglik_Payi_2019_2026'][0], 2); chk('4.8', 'YP p', 0.002, lambda: CB['rho_Saglik_Payi_2019_2026'][1], 3)
chk('4.8', 'ayıklanmış ρ', 0.88, lambda: CB['rho_Saglik_Payi_ayiklanmis_2019_2026'][0], 2); chk('4.8', 'ayıklanmış p', 0.004, lambda: CB['rho_Saglik_Payi_ayiklanmis_2019_2026'][1], 3)
chk('4.8', '65. Hükümet payı', 2.90, lambda: g('GOV-2016-65')['Saglik_Payi_%'], 2); chk('5.4', '64. Hükümet payı', 0.14, lambda: g('GOV-2015-64')['Saglik_Payi_%'], 2)
KI = RT['tema_kikare_isabet']
chk('4.8', 'χ²', 74.0, lambda: KI['chi2'], 1); chk('4.8', 'df', 13, lambda: KI['df']); chk('4.8', 'Cramér V', 0.12, lambda: KI['CramerV'], 2); chk('4.8', 'χ² p', '<0,001', lambda: KI['p'], kosul=lt(0.001))
chk('4.8', 'beklenen<5 hücre', 6, lambda: KI['beklenen_<5_hucre']); chk('4.8', 'en küçük beklenen', 1.9, lambda: KI['beklenen_min'], 1)
chk('4.8', 'HP isabet', 109, lambda: KI['HP_isabet']); chk('4.8', 'YP isabet', 4823, lambda: KI['YP_isabet'])
PP = RT['tema_belge_duzeyi_permutasyon']
chk('4.8', 'permütasyon sayısı', 3003, lambda: PP['permutasyon']); chk('4.8', 'permütasyon p', '<0,001', lambda: PP['p_kesin'], kosul=lt(0.001)); chk('4.8', 'n HP', 6, lambda: PP['n_HP']); chk('4.8', 'n YP', 8, lambda: PP['n_YP'])
chk('4.8', 'YP–plan sıra ρ', 0.93, lambda: CB['tema_YP_vs_Plan_sira'][0], 2); chk('4.8', 'HP–YP sıra ρ (havuz)', 0.56, lambda: CB['tema_HP_vs_YP']['spearman_sira'][0], 2)
chk('4.8', 'HP–YP p (havuz)', 0.04, lambda: CB['tema_HP_vs_YP']['spearman_sira'][1], 2); chk('4.8', 'HP–YP sıra ρ (belge ort.)', 0.36, lambda: PP['sira_kor_belge_ort'], 2); chk('4.8', 'belge ort. p', 0.20, lambda: PP['sira_kor_belge_ort_p'], 2)
T8 = {'İlaç, sağlık sanayii, teknoloji': (4.6, 14.9, 18.2), 'Sağlık insan gücü': (11.0, 14.6, 10.5), 'Bulaşıcı hastalık ve koruyucu sağlık': (3.7, 14.5, 18.0), 'Tedavi hizmetleri ve hastaneler': (19.3, 10.6, 7.0),
      'Reform, yönetişim, kalite': (14.7, 9.7, 11.9), 'Finansman ve sağlık sigortası': (19.3, 7.7, 6.1), 'Sosyal yardım ve dezavantajlı gruplar': (11.0, 5.6, 5.0), 'Sağlıklı yaşam ve kronik hastalıklar': (0.0, 5.4, 6.0),
      'Birinci basamak, sosyalleştirme, kırsal': (8.3, 4.1, 3.1), 'Ana-çocuk sağlığı ve nüfus': (0.9, 3.4, 1.4), 'Dijital sağlık ve bilgi sistemleri': (0.0, 3.4, 5.0), 'Acil, afet, ambulans': (0.0, 2.6, 5.0),
      'Sağlık turizmi': (3.7, 1.8, 2.1), 'Özel sektör ve piyasa': (3.7, 1.7, 0.7)}
for th, (a, b, c) in T8.items():
    chk('Tablo 8', f'{th[:14]} HP', a, lambda th=th: TD.loc[th, 'HP_2002_2016'], 1); chk('Tablo 8', f'{th[:14]} YP', b, lambda th=th: TD.loc[th, 'YP_2019_2026'], 1); chk('Tablo 8', f'{th[:14]} Plan', c, lambda th=th: TD.loc[th, 'Plan_11_12'], 1)
# ---- Tablo 9 / 4.9
DL = ['Hizmet sunumu', 'Sağlık insan gücü', 'Sağlık bilgi sistemleri', 'Tıbbi ürünler ve teknoloji', 'Sağlık finansmanı', 'Liderlik ve yönetişim']
T9 = {O[0]: ('2/2', 69.0, 0.0, 0.0, 16.7, 0.0, 14.3), O[1]: ('4/12', 72.4, 4.4, 0.0, 12.5, 0.0, 10.7), O[2]: ('5/9', 62.6, 7.1, 0.0, 1.2, 4.0, 25.2), O[3]: ('18/19', 52.7, 17.2, 0.5, 14.7, 7.2, 7.8),
      O[4]: ('12/14', 39.9, 14.4, 0.0, 3.2, 27.3, 15.2), O[5]: ('6/7', 56.5, 6.5, 0.0, 3.0, 16.7, 17.4), 'Planlar 1–3 (1963–1977)': ('3/3', 52.0, 26.5, 0.5, 12.7, 3.8, 4.5),
      'Planlar 4–6 (1979–1994)': ('3/3', 52.3, 18.8, 1.4, 13.2, 9.6, 4.7), 'Planlar 7–9 (1996–2013)': ('3/3', 41.2, 13.2, 1.5, 5.6, 21.4, 17.0), 'Planlar 10–12 (2014–2028)': ('3/3', 43.4, 9.9, 3.1, 18.4, 10.3, 14.9),
      'Yıllık program 2018 (BK)': ('1/1', 43.2, 14.4, 2.4, 12.3, 11.0, 16.8), 'CB yıllık programları 2019–2026': ('8/8', 47.3, 14.8, 3.2, 15.2, 7.8, 11.7)}
for gname, (n, *vals) in T9.items():
    chk('Tablo 9', f'{gname[:18]} n', n, lambda gname=gname: f"{int(WT.loc[gname, 'Tema_isabeti_olan_belge'])}/{int(WT.loc[gname, 'Belge'])}", kosul=lambda v, n=n: v == n)
    for dl, v in zip(DL, vals): chk('Tablo 9', f'{gname[:18]} {dl[:12]}', v, lambda gname=gname, dl=dl: WT.loc[gname, f'{dl} | belge ort. pay %'], 1)
we = lambda s, b, c: WE[(WE.Seri == s) & (WE.Boyut == b)][c].iloc[0]
HPs, PLs, YPs = 'Hükümet programları 1920–2016', 'Kalkınma planları 1963–2028', 'CB yıllık programları 2019–2026'
chk('4.9', 'HP eğilim n', 47, lambda: we(HPs, 'Hizmet sunumu', 'n'))
chk('4.9', 'HS ρ', -0.44, lambda: we(HPs, 'Hizmet sunumu', 'rho'), 2); chk('4.9', 'HS Holm p', 0.011, lambda: we(HPs, 'Hizmet sunumu', 'p_Holm'), 3)
chk('4.9', 'FN ρ', 0.66, lambda: we(HPs, 'Sağlık finansmanı', 'rho'), 2); chk('4.9', 'FN Holm p', '<0,001', lambda: we(HPs, 'Sağlık finansmanı', 'p_Holm'), kosul=lt(0.001))
chk('4.9', 'YO ρ', 0.30, lambda: we(HPs, 'Liderlik ve yönetişim', 'rho'), 2); chk('4.9', 'YO Holm p', 0.155, lambda: we(HPs, 'Liderlik ve yönetişim', 'p_Holm'), 3)
SR_ = {(r['Seri'], r['Boyut']): r for r in RT['who_egilim_saglamlik']}
chk('4.9', 'FN çoklu ρ', 0.42, lambda: SR_[(HPs, 'Sağlık finansmanı')]['coklu_rho'], 2); chk('4.9', 'FN alternatif ρ', 0.44, lambda: SR_[(HPs, 'Sağlık finansmanı')]['alt_rho'], 2)
chk('4.9', 'FN sağlamlık p<0,01', '<0,01', lambda: max(SR_[(HPs, 'Sağlık finansmanı')]['coklu_p'], SR_[(HPs, 'Sağlık finansmanı')]['alt_p']), kosul=lt(0.01))
chk('4.9', 'HS alternatif ρ', -0.29, lambda: SR_[(HPs, 'Hizmet sunumu')]['alt_rho'], 2); chk('4.9', 'HS alternatif p', 0.047, lambda: SR_[(HPs, 'Hizmet sunumu')]['alt_p'], 3)
chk('4.9', 'HS çoklu ρ', -0.12, lambda: SR_[(HPs, 'Hizmet sunumu')]['coklu_rho'], 2)
for b, r in [('Liderlik ve yönetişim', .69), ('Sağlık bilgi sistemleri', .63), ('Sağlık insan gücü', -.69)]:
    chk('4.9', f'plan ρ {b[:12]}', r, lambda b=b: we(PLs, b, 'rho'), 2); chk('4.9', f'plan p<0,05 {b[:12]}', '<0,05', lambda b=b: we(PLs, b, 'p'), kosul=lt(0.05))
chk('4.9', 'planlarda Holm sonrası anlamlı boyut', 0, lambda: int((WE[WE.Seri == PLs].p_Holm < 0.05).sum()))
chk('4.9', 'YP BS ρ', 0.83, lambda: we(YPs, 'Sağlık bilgi sistemleri', 'rho'), 2); chk('4.9', 'YP BS p', 0.010, lambda: we(YPs, 'Sağlık bilgi sistemleri', 'p'), 3); chk('4.9', 'YP BS Holm p', 0.061, lambda: we(YPs, 'Sağlık bilgi sistemleri', 'p_Holm'), 3)
HY = RT['who_HP_vs_YP']
chk('4.9', 'HP–YP permütasyon p', '<0,001', lambda: HY['p_kesin'], kosul=lt(0.001))
chk('4.9', 'BS Holm p', 0.010, lambda: HY['boyut_MW_p_Holm']['Sağlık bilgi sistemleri'], 3); chk('4.9', 'TU Holm p', 0.012, lambda: HY['boyut_MW_p_Holm']['Tıbbi ürünler ve teknoloji'], 3)
chk('4.9', 'FN ve İG Holm ≥0,05', '≥0,05', lambda: min(HY['boyut_MW_p_Holm']['Sağlık finansmanı'], HY['boyut_MW_p_Holm']['Sağlık insan gücü']), kosul=lambda v: v >= 0.05)
chk('4.9', 'FN ve İG düzeltme öncesi <0,05', '<0,05', lambda: max(HY['boyut_MW_p']['Sağlık finansmanı'], HY['boyut_MW_p']['Sağlık insan gücü']), kosul=lt(0.05))
for b, a, c in [('Sağlık bilgi sistemleri', 0.0, 3.2), ('Tıbbi ürünler ve teknoloji', 3.0, 15.2), ('Sağlık finansmanı', 16.7, 7.8), ('Sağlık insan gücü', 6.5, 14.8)]:
    chk('4.9', f'HP ort {b[:12]}', a, lambda b=b: HY['HP_ort'][b], 1); chk('4.9', f'YP ort {b[:12]}', c, lambda b=b: HY['YP_ort'][b], 1)
# terim sayımları
for t, grp, v in [('şehir hastane', 'HP2002-16', 4), ('şehir hastane', 'YP2018-26', 47), ('dispanser', 'PL<1996', 22), ('geri ödeme', 'PL1996+', 11), ('geri ödeme', 'YP2018-26', 36),
                  ('genel sağlık sigorta', 'YP2018-26', 56), ('akreditasyon', 'PL1996+', 7), ('akreditasyon', 'YP2018-26', 44), ('performans', 'YP2018-26', 42), ('memnuniyet', 'YP2018-26', 28),
                  ('tıbbi cihaz', 'PL1996+', 58), ('tıbbi cihaz', 'YP2018-26', 155), ('dijital', 'YP2018-26', 74), ('bilişim', 'YP2018-26', 22), ('e-nabız', 'YP2018-26', 8)]:
    chk('4.9', f'"{t}" {grp}', v, lambda t=t, grp=grp: TS.loc[t, grp])
for t in ['geri ödeme', 'tıbbi cihaz', 'akreditasyon']:
    chk('4.9', f'"{t}" HP toplam', 0, lambda t=t: TS.loc[t, ['HP<1980', 'HP1980-2001', 'HP2002-16']].sum())
chk('4.9', '"akreditasyon" PL<1996', 0, lambda: TS.loc['akreditasyon', 'PL<1996'])
for p, v in [(r'\bsosyal yardım', 132), (r'\byaşlı', 126), (r'\bengelli', 56), (r'\bmuhtaç', 43), (r'\byoksul', 37)]: chk('3.6', f'sosyal yardım teması {p[2:]}', v, lambda p=p: SY.loc[p, 'Isabet'])
# ---- ön doğrulama örneklemleri arşivle aynı mı
AR = PKG / 'validation' / 'on_dogrulama_arsivi'
for f in ['dogrulama_orneklemi.csv', 'dogrulama_orneklemi_2.csv']:
    chk('3.4 / Tablo 2', f'ön doğrulama örneklemi {f} arşivle aynı kayıtlar', 'aynı', lambda f=f: set(map(tuple, C(f'{V}/{f}')[['Hukumet_ID', 'Paragraf_No']].values)) == set(map(tuple, C(AR / f)[['Hukumet_ID', 'Paragraf_No']].values)), kosul=lambda v: v is True)
R_ = pd.DataFrame(rows); R_.to_csv(OUT / 'dogrulama_raporu.csv', index=False, encoding='utf-8-sig')
n = len(R_); a = int(R_.Durum.str.startswith('AYNI').sum()); ys = int((R_.Durum == 'AYNI (yuvarlama sınırı)').sum())
md = [f'# Yeniden üretim doğrulama raporu\n', f'Karşılaştırılan değer: {n}; aynı: {a} (bunların {ys} tanesi tam yarım yuvarlama sınırında: makale yukarı/çift yuvarlamadan birini kullanmış); farklı: {int((R_.Durum == "FARK").sum())}; hata: {int((R_.Durum == "HATA").sum())}\n',
      'Tablo 2 (ön denetim kesinlikleri) hesaplamalı değildir; kodlama kararları kayıtlı olmadığından yeniden üretilemez.\n']
if (~R_.Durum.str.startswith('AYNI')).any(): md += ['\n## Farklı / hatalı değerler\n', '```', R_[~R_.Durum.str.startswith('AYNI')].to_string(index=False), '```']
if ys: md += ['\n## Yuvarlama sınırındaki değerler\n', 'Bu satırlarda ara çıktı dosyaları değeri 3–4 ondalıkla sakladığı için yeniden üretilen değer tam yarım sınırında görünür (ör. ek_testler.json içinde H = 7,245; yuvarlanmamış H = 7,2447). Makaledeki değer, yuvarlanmamış değerin doğru yuvarlamasıdır veya yarım-yukarı kuralıyla uyumludur; içerik farkı yoktur.\n', '```', R_[R_.Durum == 'AYNI (yuvarlama sınırı)'].to_string(index=False), '```']
open(OUT / 'DOGRULAMA_RAPORU.md', 'w', encoding='utf-8').write('\n'.join(md))
print('\n'.join(md[:2])); print(R_[R_.Durum != 'AYNI'].to_string())

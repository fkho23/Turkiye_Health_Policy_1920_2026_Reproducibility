"""s14 — Makaledeki tabloların analiz çıktılarından derlenmesi ve tablo/şekil–kod–veri eşleştirme tablosu.
Çıktılar: outputs/tablolar/Tablo_*.csv, Ek_Tablo_*.csv, Makale_Tablolari.xlsx, Tablo_Sekil_Eslestirme.csv"""
import os, sys, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

ORDER = ['1920-1923 Meclis Hükümetleri', '1923-1946 Tek Parti', '1946-1960 Çok Partili Dönem', '1960-1980 Planlı Dönem', '1980-2002 Neoliberal Dönüşüm', '2002-2018 AK Parti Dönemi']
T = {}
B = pd.read_csv(f'{RV}/belge_envanteri.csv')
B['Tur2'] = B.Tur.replace({'Yıllık program (Bakanlar Kurulu)': 'Yıllık program', 'Cumhurbaşkanlığı yıllık programı': 'Yıllık program'})
t1 = B.groupby('Tur2').agg(Belge=('Belge_ID', 'size'), Toplam_kelime=('Toplam_Kelime', 'sum'), Saglik_cumlesi=('Saglik_Cumle_Sayisi', 'sum')).reindex(['Hükümet programı', 'Kalkınma planı', 'Yıllık program'])
t1.loc['Toplam'] = t1.sum(); T['Tablo_1_Korpus'] = t1.reset_index()
DS = pd.read_csv(f'{V}/donem_ozet.csv'); EK = json.load(open(f'{V}/ek_testler.json', encoding='utf-8'))
bs = EK['Donem_medyan_bootstrap']
T['Tablo_4_Donem_saglik_payi'] = pd.DataFrame([dict(Donem=r.Donem, n=r.Hukumet_Sayisi, Ortalama_uzunluk=r.Ort_Kelime, Havuz_payi=r['Havuz_Saglik_Payi_%'], Medyan_pay=r['Medyan_Saglik_Payi_%'],
    GA95_alt=bs.get(r.Donem, {}).get('GA95', [None, None])[0], GA95_ust=bs.get(r.Donem, {}).get('GA95', [None, None])[1], Terim_1000=r.Ort_Terim_1000,
    Saglik_icermeyen=r.Saglik_Bolumu_Olmayan) for _, r in DS.iterrows()])
T['Tablo_5_Saglamlik'] = pd.read_csv(f'{RV}/tablo5_duzeltilmis.csv')
LL = pd.read_csv(f'{V}/donem_ayirt_edici_terimler.csv'); T['Tablo_6_Ayirt_edici_terimler'] = LL.groupby('Donem').head(8)
T['Tablo_7_Yillik_programlar'] = pd.read_csv(f'{V}/cumhurbaskanligi_donemi_belgeler.csv')
T['Tablo_8_Tema_dagilimi'] = pd.read_csv(f'{V}/cumhurbaskanligi_donemi_tema_dagilimi.csv').sort_values('YP_2019_2026', ascending=False)
W = pd.read_csv(f'{RV}/who_boyut_donem_tablosu.csv')
T['Tablo_9_DSO_boyutlari'] = W[['Grup', 'Belge', 'Tema_isabeti_olan_belge'] + [c for c in W.columns if c.endswith('belge ort. pay %')]]
T['Tablo_3_DSO_eslestirme'] = pd.read_csv(f'{RV}/who_eslestirme_matrisi.csv')
T['Ek_Tablo_E1_Tema_egilim'] = pd.read_csv(f'{RV}/tema_egilim_holm_uzunluk.csv')
T['Ek_Tablo_E2_Plan_duzeyi'] = pd.read_csv(f'{RV}/plan_duzeyi_karsilastirma.csv')
T['Ek_Tablo_E3_Saglik_LL'] = pd.read_csv(f'{RV}/saglik_cumleleri_ayirt_edici_terimler.csv').groupby('Donem').head(8)
with pd.ExcelWriter(f'{TAB}/Makale_Tablolari.xlsx') as w:
    for k, d in T.items():
        d.to_csv(f'{TAB}/{k}.csv', index=False, encoding='utf-8-sig'); d.to_excel(w, sheet_name=k[:31], index=False)
M = [
 ('Tablo 1', 'Korpus', 's09_cumle_veri_seti.py → s14', 'veri/revizyon/belge_envanteri.csv', 'tablolar/Tablo_1_Korpus.csv'),
 ('Tablo 2', 'Ön denetim (kesinlik)', 'HESAPLAMALI DEĞİL', 'Örneklemler: s03 (seed 42/7) → veri/dogrulama_orneklemi*.csv; kararlar kayıtlı değil', '—'),
 ('Tablo 3', 'Kod kitabı ve DSÖ eşleştirmesi', 'sozlukler.py; s10_revizyon_analizleri.py', 'veri/revizyon/who_eslestirme_matrisi.csv; veri/saglik_paragraflari.xlsx (Kod_Kitabi)', 'tablolar/Tablo_3_DSO_eslestirme.csv'),
 ('Tablo 4', 'Dönemlere göre sağlık payı', 's03_analiz.py; s06_ek_testler.py', 'veri/donem_ozet.csv; veri/ek_testler.json', 'tablolar/Tablo_4_Donem_saglik_payi.csv'),
 ('Tablo 5', 'Sağlamlık (KW, Spearman)', 's10_revizyon_analizleri.py', 'veri/revizyon/tablo5_duzeltilmis.csv', 'tablolar/Tablo_5_Saglamlik.csv'),
 ('Tablo 6', 'Ayırt edici terimler', 's03_analiz.py', 'veri/donem_ayirt_edici_terimler.csv', 'tablolar/Tablo_6_Ayirt_edici_terimler.csv'),
 ('Tablo 7', 'Yıllık programlar 2018–2026', 's07_cumhurbaskanligi_donemi.py', 'veri/cumhurbaskanligi_donemi_belgeler.csv', 'tablolar/Tablo_7_Yillik_programlar.csv'),
 ('Tablo 8', 'Tema dağılımı HP–YP–Plan', 's07_cumhurbaskanligi_donemi.py; s10 (permütasyon)', 'veri/cumhurbaskanligi_donemi_tema_dagilimi.csv; veri/revizyon/revizyon_testleri.json', 'tablolar/Tablo_8_Tema_dagilimi.csv'),
 ('Tablo 9', 'DSÖ yönetsel boyutları', 's10_revizyon_analizleri.py', 'veri/revizyon/who_boyut_donem_tablosu.csv', 'tablolar/Tablo_9_DSO_boyutlari.csv'),
 ('Ek Tablo E1', 'Tema eğilimi, Holm, uzunluk', 's10_revizyon_analizleri.py', 'veri/revizyon/tema_egilim_holm_uzunluk.csv', 'tablolar/Ek_Tablo_E1_Tema_egilim.csv'),
 ('Ek Tablo E2', 'Plan düzeyi karşılaştırma', 's05_saglamlik_testleri.py (eşleştirme); s10', 'veri/program_plan_eslestirme.csv; veri/revizyon/plan_duzeyi_karsilastirma.csv', 'tablolar/Ek_Tablo_E2_Plan_duzeyi.csv'),
 ('Ek Tablo E3', 'Sağlık cümlelerinde ayırt edici terimler', 's10_revizyon_analizleri.py', 'veri/revizyon/saglik_cumleleri_ayirt_edici_terimler.csv', 'tablolar/Ek_Tablo_E3_Saglik_LL.csv'),
 ('Şekil 1', 'HP sağlık payı', 's08_sekiller_1_4.py', 'veri/hukumet_saglik_metrikleri.csv; veri/donem_ozet.csv', 'sekiller/Sekil_1_hukumet_programlari_saglik_payi.png'),
 ('Şekil 2', 'Uzunluk ve mutlak sağlık metni', 's08_sekiller_1_4.py', 'veri/hukumet_saglik_metrikleri.csv', 'sekiller/Sekil_2_uzunluk_ve_mutlak_saglik.png'),
 ('Şekil 3', 'Belge türlerine göre pay', 's08_sekiller_1_4.py', 'veri/hukumet_saglik_metrikleri.csv; veri/karsilastirma_korpuslari_metrikleri.csv', 'sekiller/Sekil_3_belge_turleri_karsilastirma.png'),
 ('Şekil 4', 'Dönem × tema ısı haritası', 's08_sekiller_1_4.py', 'veri/donem_tema_varlik_yuzde.csv', 'sekiller/Sekil_4_donem_tema_isi_haritasi.png'),
 ('Şekil 5', 'DSÖ boyutları ısı haritası', 's11_who_sekil.py', 'veri/revizyon/who_boyut_donem_tablosu.csv', 'sekiller/Sekil_5_who_yonetsel_boyutlar.png'),
 ('Metin 4.1–4.3', 'KW, ε², Spearman, Mann-Whitney, bootstrap', 's03_analiz.py; s06_ek_testler.py', 'veri/istatistik_testleri.json; veri/ek_testler.json', '—'),
 ('Metin 4.4', 'L-basıklık, Monte Carlo p', 's10_revizyon_analizleri.py', 'veri/revizyon/l_basiklik.csv', '—'),
 ('Metin 4.5', 'Plan/yıllık program eğilimi, Wilcoxon', 's05_saglamlik_testleri.py; s10', 'veri/saglamlik_testleri.json; veri/revizyon/revizyon_testleri.json', '—'),
 ('Metin 4.6', 'Tema payları, varlık, Holm, uzunluk', 's03_analiz.py; s10', 'veri/donem_tema_pay_yuzde.csv; veri/donem_tema_varlik_yuzde.csv; veri/revizyon/tema_egilim_holm_uzunluk.csv', '—'),
 ('Metin 4.8', 'Yıllık program testleri, ki-kare, permütasyon', 's07; s10', 'veri/cumhurbaskanligi_donemi_testler.json; veri/revizyon/revizyon_testleri.json', '—'),
 ('Metin 4.9', 'DSÖ eğilimleri, belge türü karşılaştırması', 's10', 'veri/revizyon/who_boyut_egilim.csv; veri/revizyon/revizyon_testleri.json', '—'),
 ('Metin 3.6 ve 4.9', 'Terim sıklıkları', 's16_terim_sayimlari.py', 'veri/revizyon/terim_sayimlari_gruplar.csv; veri/revizyon/sosyal_yardim_terimleri.csv', '—'),
 ('Doğrulama formu', '160 + 266 kayıt, iki kör form', 's12_dogrulama_formlari.py', 'outputs/dogrulama/', '—'),
 ('Uyum istatistikleri', 'kappa, precision, recall, F1', 's13_kodlayici_uyumu.py (insan değerlendirmesi sonrası)', 'outputs/dogrulama/kodlayici_uyumu_sonuclari.json', '—')]
EM = pd.DataFrame(M, columns=['Makale_ogesi', 'Icerik', 'Kod', 'Veri_dosyasi', 'Uretilen_cikti'])
EM['Cikti_mevcut'] = EM.Uretilen_cikti.map(lambda p: '—' if p == '—' else ('evet' if os.path.exists(OUT / p) else 'HAYIR'))
EM.to_csv(f'{TAB}/Tablo_Sekil_Eslestirme.csv', index=False, encoding='utf-8-sig')
print(EM.to_string())

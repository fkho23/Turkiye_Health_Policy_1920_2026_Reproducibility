"""s16 — Makale bölüm 3.6 ve 4.9'daki terim sıklıkları (yalnızca sağlık cümlelerinde).
Revizyon sırasında yapılan sayımın kodlanmış hâlidir; sayım kuralı: küçük harfe çevrilmiş cümlede r'\\b'+terim kalıbının geçiş sayısı.
Gruplar: HP<1980, HP1980-2001, HP2002-16, PL<1996 (başlangıç yılı), PL1996+, YP2018-26.
Çıktılar: veri/revizyon/terim_sayimlari_gruplar.csv, veri/revizyon/sosyal_yardim_terimleri.csv"""
import os, re, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

S = pd.read_csv(f'{RV}/saglik_cumleleri.csv.gz')
n_ = lambda s: s.replace('I', 'ı').replace('İ', 'i').lower()
S['n'] = S.Cumle.map(n_)


def grp(r):
    if r.Tur == 'Hükümet programı': return 'HP<1980' if r.Yil < 1980 else ('HP1980-2001' if r.Yil < 2002 else 'HP2002-16')
    if r.Tur == 'Kalkınma planı': return 'PL<1996' if r.Yil < 1996 else 'PL1996+'
    return 'YP2018-26'


S['g'] = S.apply(grp, axis=1)
TERMS = {'T10': ['teşkilat', 'reform', 'yeniden yapılan', 'verimlilik', 'performans', 'kalite', 'akreditasyon', 'hasta hak', 'memnuniyet', 'dönüşüm', 'koordinasyon', 'denetim'],
         'T02': ['hastane', 'şehir hastane', 'yatak', 'tedavi', 'poliklinik', 'dispanser'],
         'T07': ['ilaç', 'tıbbi cihaz', 'sağlık sanayi', 'biyoteknoloj', 'aşı üret', 'yerli'],
         'T11': ['e-sağlık', 'bilgi sistem', 'elektronik', 'dijital', 'bilişim', 'e-nabız', 'veri taban', 'tele'],
         'T05': ['sigorta', 'genel sağlık sigorta', 'yeşil kart', 'finansman', 'prim', 'geri ödeme', 'döner sermaye', 'katkı pay'],
         'T03': ['hekim', 'hemşire', 'ebe', 'sağlık personel', 'uzman', 'tıp fakülte', 'insan gücü'],
         'T06': ['özel sektör', 'kamu-özel', 'kamu özel', 'özel hastane', 'özelleştir', 'hizmet alım']}
G = ['HP<1980', 'HP1980-2001', 'HP2002-16', 'PL<1996', 'PL1996+', 'YP2018-26']
rows = []
for t, ts in TERMS.items():
    for w in ts:
        r = {'Tema': t, 'Terim': w}
        for g in G: r[g] = int(S[S.g == g].n.str.count(r'\b' + re.escape(w)).sum())
        rows.append(r)
pd.DataFrame(rows).to_csv(f'{RV}/terim_sayimlari_gruplar.csv', index=False, encoding='utf-8-sig')
pd.DataFrame({'Grup': G, 'Saglik_cumlesi': [int((S.g == g).sum()) for g in G]}).to_csv(f'{RV}/terim_sayimlari_payda.csv', index=False, encoding='utf-8-sig')
# sosyal yardım teması isabetlerinin terim dağılımı (bölüm 3.6)
ps = [r'\bmuavenet', r'\bsosyal yardım', r'\byoksul', r'\bfakir', r'\bengelli', r'\bözürlü', r'\bsakat', r'\byaşlı', r'\bkimsesiz', r'\bdüşkün',
      r'\bbakım(?:evi|evleri| hizmet| ve rehabilitasyon)', r'\bevde bakım', r'\bhimaye', r'\bmuhtaç', r'\bücretsiz']
sub = S[S['T09_Sosyal_yardim_ve_dezavantajli_gruplar'] > 0]
pd.DataFrame([(p, int(sum(len(re.findall(p, x)) for x in sub.n))) for p in ps], columns=['Kalip', 'Isabet']).sort_values('Isabet', ascending=False)\
  .to_csv(f'{RV}/sosyal_yardim_terimleri.csv', index=False, encoding='utf-8-sig')
print(pd.DataFrame(rows).to_string())

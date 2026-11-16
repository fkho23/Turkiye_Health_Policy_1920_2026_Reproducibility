"""s07 — Özgün: 07_cumhurbaskanligi_donemi.py (yalnızca yollar değişti).
07_cumhurbaskanligi_donemi.py — 2018–2026: hükümet programı türü sona erdikten sonra yürütmenin sağlık önceliği.
Belgeler: 2018 Bakanlar Kurulu yıllık programı, 2019–2026 Cumhurbaşkanlığı yıllık programları, 11. ve 12. Kalkınma Planları.
Ölçüt Makale 1 ile aynıdır (cümle düzeyi sağlık sözlüğü, 02_analiz.py). Duyarlılık için makroekonomik salgın cümleleri
ve tablo satırları çıkarılarak pay yeniden hesaplanır (kurallar aşağıda; Makale 2'deki ayıklama kurallarıyla aynıdır)."""
import os,re,json
import pandas as pd, numpy as np
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import sozlukler as _soz; ns = dict(vars(_soz))
norm,mask,hsent,words,HRE,TRE,TLABEL=[ns[k] for k in ('norm','mask','hsent','words','HRE','TRE','TLABEL')]
MACRO=re.compile(r'(maliye politika|mali destek|ekonomik ve sosyal etki|ekonomik etki|toparlanma|resesyon|ekonomik faaliyet|gsyh|büyüme|enflasyon|petrol|emtia|finansal koşul|piyasa|talep|tüketici|yatırımcı|konut|ihracat|ithalat|döviz|kur |faiz|istihdam|işsizlik|turist|küresel ekonomi|dış ticaret|kredi)')
SALGIN_ONLY=re.compile(r'^(salgın|pandemi|covid)')
TABLE=re.compile(r'\(yüzde\)|\(milyon|\(milyar|\(s\)|bakanlığı.{0,60}bakanlığı.{0,60}bakanlığı|\b(?:ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık) sonu\b')
def etiket(c):
    n=mask(norm(c)); ms=[m.group(0) for m in HRE.finditer(n)]
    if TABLE.search(n) or len(words(c))>90: return 'tablo'
    if ms and all(SALGIN_ONLY.match(x) for x in ms) and MACRO.search(n): return 'makro_salgin'
    return 'politika'
IDS=['PRES-2018-YP']+[f'PRES-{y}' for y in range(2019,2027)]+['DEVPLAN-11','DEVPLAN-12']
rows=[]
for i in IDS:
    paras=open(f'{TXT_COMP}/{i}.txt',encoding='utf-8').read().split('\n\n')
    tot=sum(len(words(p)) for p in paras); hw=0; pw=0; nm=0; nt=0; t01=0; tall=0; t01p=0; tallp=0
    for p in paras:
        for c in hsent(p):
            w=len(words(c)); hw+=w; e=etiket(c); n=mask(norm(c))
            hits={k:len(r.findall(n)) for k,r in TRE.items()}; s=sum(hits.values())
            t01+=hits['T01_Bulasici_hastalik_ve_koruyucu_saglik']; tall+=s
            if e=='politika': pw+=w; t01p+=hits['T01_Bulasici_hastalik_ve_koruyucu_saglik']; tallp+=s
            elif e=='makro_salgin': nm+=1
            else: nt+=1
    y=2018 if i=='PRES-2018-YP' else (int(i[5:]) if i.startswith('PRES') else {'DEVPLAN-11':2019,'DEVPLAN-12':2024}[i])
    rows.append(dict(ID=i,Yil=y,Toplam_Kelime=tot,Saglik_Payi=round(hw/tot*100,2),Saglik_Payi_ayiklanmis=round(pw/tot*100,2),
        Makro_salgin_cumle=nm,Tablo_cumle=nt,T01_tema_payi=round(t01/tall*100,1),T01_tema_payi_ayiklanmis=round(t01p/tallp*100,1)))
D=pd.DataFrame(rows); D.to_csv(f'{V}/cumhurbaskanligi_donemi_belgeler.csv',index=False,encoding='utf-8-sig'); print(D.to_string())
Y=D[D.ID.str.match(r'PRES-20(19|2)')]
out={}
for k in ['Saglik_Payi','Saglik_Payi_ayiklanmis']:
    r=stats.spearmanr(Y.Yil,Y[k]); out[f'rho_{k}_2019_2026']=[round(float(r.statistic),3),round(float(r.pvalue),4)]
# tema dağılımı: AK Parti dönemi hükümet programları (2002–2016) vs CB yıllık programları (2019–2026) vs 11.–12. Planlar
H=pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv'); K=pd.read_csv(f'{V}/karsilastirma_korpuslari_metrikleri.csv')
TK=list(TLABEL); TL=[TLABEL[k] for k in TK]
g1=H[H.Yil>=2002][TK].sum().values; g2=K[K.ID.str.match(r'PRES-20(19|2)')][TL].sum().values; g3=K[K.ID.isin(['DEVPLAN-11','DEVPLAN-12'])][TL].sum().values
T=pd.DataFrame({'Tema':TL,'HP_2002_2016':(g1/g1.sum()*100).round(1),'YP_2019_2026':(g2/g2.sum()*100).round(1),'Plan_11_12':(g3/g3.sum()*100).round(1)})
T['Fark_YP_HP']=(T.YP_2019_2026-T.HP_2002_2016).round(1); T.to_csv(f'{V}/cumhurbaskanligi_donemi_tema_dagilimi.csv',index=False,encoding='utf-8-sig')
print(T.sort_values('YP_2019_2026',ascending=False).to_string()); print('isabet n:',g1.sum(),g2.sum(),g3.sum())
ch=stats.chi2_contingency(np.vstack([g1,g2])); cv=np.sqrt(ch[0]/(g1.sum()+g2.sum())/1)
r=stats.spearmanr(g1,g2); out['tema_HP_vs_YP']={'chi2':round(float(ch[0]),1),'df':int(ch[2]),'p':float(ch[1]),'CramerV':round(float(cv),3),'spearman_sira':[round(float(r.statistic),3),round(float(r.pvalue),4)]}
r=stats.spearmanr(g2,g3); out['tema_YP_vs_Plan_sira']=[round(float(r.statistic),3),round(float(r.pvalue),4)]
json.dump(out,open(f'{V}/cumhurbaskanligi_donemi_testler.json','w',encoding='utf-8'),ensure_ascii=False,indent=1); print(out)

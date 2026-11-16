"""s05 — Özgün: 05_saglamlik_testleri.py (yalnızca yollar değişti).
05_saglamlik_testleri.py — duyarlılık/sağlamlık analizleri"""
import os,json
import pandas as pd
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
H=pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv'); K=pd.read_csv(f'{V}/karsilastirma_korpuslari_metrikleri.csv')
out={}
def kw(df,col):
    g=[x[col].values for _,x in df.groupby('Donem') if len(x)>=3]
    h,p=stats.kruskal(*g); return {'H':round(h,3),'p':round(p,4),'n':int(len(df)),'grup':len(g)}
def sp(x,y):
    r,p=stats.spearmanr(x,y); return {'rho':round(r,3),'p':round(p,4),'n':int(len(x))}
for lab,df in [('tum_programlar',H),('500_kelime_ve_ustu',H[H.Toplam_Kelime>=500]),('1923_sonrasi_IVH_haric',H[~H.Hukumet_ID.str.contains('IVH')])]:
    out[lab]={'KW_Donem_SaglikPayi':kw(df,'Saglik_Payi_%'),'KW_Donem_ParagrafPayi':kw(df,'Saglik_Paragraf_Payi_%'),
              'KW_Donem_Terim1000':kw(df,'Saglik_Terim_1000'),'Spearman_Yil_SaglikPayi':sp(df.Yil,df['Saglik_Payi_%']),
              'Spearman_Yil_Terim1000':sp(df.Yil,df.Saglik_Terim_1000),'Spearman_Yil_ParagrafPayi':sp(df.Yil,df['Saglik_Paragraf_Payi_%'])}
# Sağlık içeriği hiç olmayan programlar
z=H[H['Saglik_Payi_%']==0]; out['saglik_icerigi_olmayan']=z[['Hukumet_ID','Yil','Toplam_Kelime']].to_dict('records')
# 1960 öncesi vs sonrası (planlı dönem eşiği), kısa metinler hariç
L=H[H.Toplam_Kelime>=500]; a=L[L.Yil<1960]['Saglik_Payi_%']; b=L[L.Yil>=1960]['Saglik_Payi_%']
u,p=stats.mannwhitneyu(a,b); out['MW_1960_oncesi_vs_sonrasi_500+']={'U':float(u),'p':round(p,4),'medyan_once':round(a.median(),2),'medyan_sonra':round(b.median(),2),'n':[len(a),len(b)]}
# Karşılaştırma korpusları
P=K[K.Tur=='Kalkınma planı'].dropna(subset=['Saglik_Payi_%']); Y=K[K.Tur!='Kalkınma planı'].dropna(subset=['Saglik_Payi_%'])
out['Kalkinma_planlari_Spearman_Yil_Pay']=sp(P.Baslangic,P['Saglik_Payi_%'])
out['Yillik_programlar_Spearman_Yil_Pay']=sp(Y.Baslangic,Y['Saglik_Payi_%'])
out['Yillik_programlar_Spearman_Yil_Terim1000']=sp(Y.Baslangic,Y.Saglik_Terim_1000)
# Aynı döneme düşen hükümet programı ile plan karşılaştırması (hükümet yılını kapsayan plan)
rows=[]
for _,h in H[H.Yil>=1963].iterrows():
    m=P[(P.Baslangic<=h.Yil)&(P.Bitis>=h.Yil)]
    if len(m): rows.append({'Hukumet_ID':h.Hukumet_ID,'Yil':int(h.Yil),'Program_Pay':h['Saglik_Payi_%'],'Plan':m.iloc[0].ID,'Plan_Pay':m.iloc[0]['Saglik_Payi_%']})
E2=pd.DataFrame(rows); E2.to_csv(f'{V}/program_plan_eslestirme.csv',index=False,encoding='utf-8-sig')
w=stats.wilcoxon(E2.Program_Pay,E2.Plan_Pay)
out['Wilcoxon_Program_vs_KapsayanPlan']={'W':float(w.statistic),'p':round(w.pvalue,6),'n':len(E2),'medyan_program':round(E2.Program_Pay.median(),2),'medyan_plan':round(E2.Plan_Pay.median(),2),'program_planin_altinda':int((E2.Program_Pay<E2.Plan_Pay).sum())}
json.dump(out,open(f'{V}/saglamlik_testleri.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))

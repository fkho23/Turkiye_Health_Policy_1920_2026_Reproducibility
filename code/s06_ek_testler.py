"""s06 — Özgün: 06_ek_testler.py (yollar ve seed kaynağı değişti; seed değeri aynı: 42).
06_ek_testler.py — etki büyüklükleri, çoklu test düzeltmesi, kesintili denge (basıklık), bootstrap GA"""
import os,json
import numpy as np, pandas as pd
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
H=pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv').sort_values(['Yil','Hukumet_ID']).reset_index(drop=True)
T=pd.read_csv(f'{V}/tema_varlik_matrisi.csv')
out={}
def kw_eps(df,col,minn=1):
    g=[x[col].values for _,x in df.groupby('Donem') if len(x)>=minn]
    h,p=stats.kruskal(*g); n=sum(len(x) for x in g); k=len(g)
    return {'H':round(h,3),'p':round(p,4),'epsilon2':round(h/((n**2-1)/(n+1)),3),'eta2_H':round((h-k+1)/(n-k),3),'n':n,'grup':k}
out['KW_Donem_6grup']=kw_eps(H,'Saglik_Payi_%')
out['KW_Donem_n3plus']=kw_eps(H,'Saglik_Payi_%',3)
# bootstrap %95 GA: dönem medyanları
rng=np.random.default_rng(seed('bootstrap_donem_medyan')); bs={}
for d,x in H.groupby('Donem'):
    v=x['Saglik_Payi_%'].values
    if len(v)<3: continue
    meds=[np.median(rng.choice(v,len(v))) for _ in range(5000)]
    bs[d]={'medyan':round(float(np.median(v)),2),'GA95':[round(float(np.percentile(meds,2.5)),2),round(float(np.percentile(meds,97.5)),2)],'n':len(v)}
out['Donem_medyan_bootstrap']=bs
# tema-yıl Spearman + Holm ve BH düzeltmesi
lab={c:c for c in T.columns if c.startswith('T')}
rows=[]
for c in [c for c in T.columns if c.startswith('T')]:
    if T[c].nunique()<2: continue
    r=stats.spearmanr(T.Yil,T[c]); rows.append([c,r.statistic,r.pvalue])
Df=pd.DataFrame(rows,columns=['Tema','rho','p']).sort_values('p').reset_index(drop=True)
m=len(Df); Df['p_Holm']=[min(1,max((m-i)*Df.p.iloc[j] for j in range(i+1))) for i in range(m)]
bh=Df.p*m/(np.arange(m)+1); Df['q_BH']=np.minimum.accumulate(bh[::-1])[::-1].clip(upper=1)
Df=Df.round(4); Df.to_csv(f'{V}/tema_yil_spearman_duzeltilmis.csv',index=False,encoding='utf-8-sig')
out['Tema_Yil_Spearman_Holm']=Df.to_dict('records')
# kesintili denge: ardışık programlar arası pay değişimlerinin basıklığı
def lmom(x):
    x=np.sort(x); n=len(x); i=np.arange(1,n+1)
    b0=x.mean(); b1=np.sum((i-1)/(n-1)*x)/n; b2=np.sum((i-1)*(i-2)/((n-1)*(n-2))*x)/n; b3=np.sum((i-1)*(i-2)*(i-3)/((n-1)*(n-2)*(n-3))*x)/n
    l2=2*b1-b0; l4=20*b3-30*b2+12*b1-b0; return l4/l2
res={}
for lab2,df in [('tum',H),('500+',H[H.Toplam_Kelime>=500])]:
    d=np.diff(df['Saglik_Payi_%'].values)
    pc=df['Saglik_Payi_%'].pct_change().replace([np.inf,-np.inf],np.nan).dropna().values
    res[lab2]={'n_degisim':len(d),'kurtosis_fisher_puan':round(float(stats.kurtosis(d)),2),'L_kurtosis_puan':round(float(lmom(d)),3),
               'kurtosis_test_p':round(float(stats.kurtosistest(d).pvalue),4),'L_kurtosis_normal_referans':0.123,
               'kurtosis_fisher_yuzde_degisim':round(float(stats.kurtosis(pc)),2),'L_kurtosis_yuzde_degisim':round(float(lmom(pc)),3)}
out['Kesintili_denge_basiklik']=res
json.dump(out,open(f'{V}/ek_testler.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))

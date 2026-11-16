"""s03 — Hükümet programları: sağlık payı, dönem/tür testleri, tema kodlaması, ayırt edici terimler, ön doğrulama örneklemleri.
Özgün: 02_analiz.py (hesaplama değiştirilmedi; sözlükler sozlukler.py'den, yollar common.py'den, seed'ler params.json'dan)."""
import os,re,json,math,subprocess,collections,random
import pandas as pd, numpy as np
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from sozlukler import *
# ---------------- 1. hükümet programları ----------------
gl=pd.read_excel(GOV_META)
gl=gl[gl['Hukumet_Programi_Var_mi']=='Var'].copy()
def yr(d): return int(str(d)[-4:])
gl['Yil']=gl['Gorev_Baslangic'].map(yr)
def period(row):
    gid=row['Hukumet_ID']; n=str(row['Hukumet_No_veya_IVH_No'])
    if 'IVH' in gid: return '1920-1923 Meclis Hükümetleri'
    n=int(n)
    if n<=14: return '1923-1946 Tek Parti'
    if n<=23: return '1946-1960 Çok Partili Dönem'
    if n<=43: return '1960-1980 Planlı Dönem'
    if n<=57: return '1980-2002 Neoliberal Dönüşüm'
    return '2002-2018 AK Parti Dönemi'
gl['Donem']=gl.apply(period,axis=1)
def gtype(t):
    t=str(t)
    if t.startswith('Koalisyon'): return 'Koalisyon'
    if t.startswith('Tek parti (azınlık)'): return 'Azınlık (tek parti)'
    if t.startswith('Tek parti'): return 'Tek parti (çoğunluk)'
    if t.startswith('Askerî'): return 'Askerî dönem'
    if 'partilerüstü' in t: return 'Partilerüstü/teknokrat'
    if 'çok partili' in t: return 'Çok partili/bağımsız katılımlı'
    return 'Meclis hükümeti'
gl['Tur_Grubu']=gl['Hukumet_Turu'].map(gtype)
P=pd.read_csv(PARAS)
P=P[~P['Metin'].str.contains(DROP)].copy()
P['norm']=P['Metin'].map(lambda s: mask(norm(s)))
P['Kelime']=P['Metin'].map(lambda s: len(words(s)))
# v4: tüm ölçütler cümle düzeyinde; sağlık cümlesi = is_h()
P['HS']=P['Metin'].map(hsent)
P['Saglik_Terim']=P['HS'].map(lambda L: sum(len(HRE.findall(mask(norm(c)))) for c in L))
P['Saglik_Paragraf']=P['HS'].map(len)>0
P['Saglik_Cumle_Kelime']=P['HS'].map(lambda L: sum(len(words(c)) for c in L))
for k,r in TRE.items(): P[k]=P['HS'].map(lambda L,r=r: sum(len(r.findall(mask(norm(c)))) for c in L))
agg=P.groupby('Hukumet_ID').agg(Toplam_Kelime=('Kelime','sum'),Paragraf=('Kelime','size'),Saglik_Paragraf=('Saglik_Paragraf','sum'),Saglik_Terim=('Saglik_Terim','sum')).reset_index()
hw=P[P.Saglik_Paragraf].groupby('Hukumet_ID')['Kelime'].sum().rename('Saglik_Kelime')
agg=agg.merge(hw,on='Hukumet_ID',how='left').fillna({'Saglik_Kelime':0})
agg['Saglik_Paragraf_Payi_%']=(agg.Saglik_Kelime/agg.Toplam_Kelime*100).round(2)
sc=P.groupby('Hukumet_ID')['Saglik_Cumle_Kelime'].sum().rename('Saglik_Cumle_Kelime')
agg=agg.merge(sc,on='Hukumet_ID')
agg['Saglik_Payi_%']=(agg.Saglik_Cumle_Kelime/agg.Toplam_Kelime*100).round(2)  # birincil: cümle düzeyi
agg['Saglik_Terim_1000']=(agg.Saglik_Terim/agg.Toplam_Kelime*1000).round(2)
th=P[P.Saglik_Paragraf].groupby('Hukumet_ID')[list(THEMES)].sum()
M=gl[['Hukumet_ID','Hukumet_No_veya_IVH_No','Resmi_Adi','Basbakan_veya_Heyet_Baskani','Gorev_Baslangic','Gorev_Bitis','Yil','Hukumet_Turu','Tur_Grubu','Donem']].merge(agg,on='Hukumet_ID').merge(th.reset_index(),on='Hukumet_ID',how='left').fillna(0)
M=M.sort_values(['Yil','Hukumet_ID']).reset_index(drop=True)
M.to_csv(f'{V}/hukumet_saglik_metrikleri.csv',index=False,encoding='utf-8-sig')
# tema varlık (en az 1 eşleşme) matrisi
TM=M[['Hukumet_ID','Yil','Donem']+list(THEMES)].copy()
for k in THEMES: TM[k]=(TM[k]>0).astype(int)
TM.to_csv(f'{V}/tema_varlik_matrisi.csv',index=False,encoding='utf-8-sig')
# dönem özetleri
order=['1920-1923 Meclis Hükümetleri','1923-1946 Tek Parti','1946-1960 Çok Partili Dönem','1960-1980 Planlı Dönem','1980-2002 Neoliberal Dönüşüm','2002-2018 AK Parti Dönemi']
def summ(df,by):
    g=df.groupby(by)
    out=pd.DataFrame({'Hukumet_Sayisi':g.size(),'Ort_Kelime':g.Toplam_Kelime.mean().round(0),'Toplam_Kelime':g.Toplam_Kelime.sum(),'Toplam_Saglik_Kelime(cumle)':g.Saglik_Cumle_Kelime.sum(),
        'Havuz_Saglik_Payi_%':(g.Saglik_Cumle_Kelime.sum()/g.Toplam_Kelime.sum()*100).round(2),'Ort_Paragraf_Payi_%':g['Saglik_Paragraf_Payi_%'].mean().round(2),'Ort_Saglik_Payi_%':g['Saglik_Payi_%'].mean().round(2),'Medyan_Saglik_Payi_%':g['Saglik_Payi_%'].median().round(2),
        'SS_Saglik_Payi':g['Saglik_Payi_%'].std().round(2),'Ort_Terim_1000':g.Saglik_Terim_1000.mean().round(2),'Saglik_Bolumu_Olmayan':g.apply(lambda x:(x.Saglik_Paragraf==0).sum())})
    return out
DS=summ(M,'Donem').reindex(order); DS.to_csv(f'{V}/donem_ozet.csv',encoding='utf-8-sig')
TS=summ(M,'Tur_Grubu').sort_values('Hukumet_Sayisi',ascending=False); TS.to_csv(f'{V}/hukumet_turu_ozet.csv',encoding='utf-8-sig')
# dönem × tema: hükümetlerin % kaçı temaya değinmiş; tema eşleşmelerinin dönem içi payı
pres=TM.groupby('Donem')[list(THEMES)].mean().reindex(order)*100
cnt=M.groupby('Donem')[list(THEMES)].sum().reindex(order); share=cnt.div(cnt.sum(axis=1),axis=0)*100
pres.round(1).rename(columns=TLABEL).to_csv(f'{V}/donem_tema_varlik_yuzde.csv',encoding='utf-8-sig')
share.round(1).rename(columns=TLABEL).to_csv(f'{V}/donem_tema_pay_yuzde.csv',encoding='utf-8-sig')
# istatistik testleri
res={}
grp=[M.loc[M.Donem==d,'Saglik_Payi_%'].values for d in order if (M.Donem==d).sum()>1]
res['KruskalWallis_Donem_SaglikPayi']=dict(zip(['H','p'],map(float,stats.kruskal(*grp))))
grp2=[M.loc[M.Tur_Grubu==t,'Saglik_Payi_%'].values for t in M.Tur_Grubu.unique() if (M.Tur_Grubu==t).sum()>2]
res['KruskalWallis_Tur_SaglikPayi(n>2 gruplar)']=dict(zip(['H','p'],map(float,stats.kruskal(*grp2))))
rho=stats.spearmanr(M.Yil,M['Saglik_Payi_%']); res['Spearman_Yil_SaglikPayi']={'rho':float(rho.statistic),'p':float(rho.pvalue)}
rho=stats.spearmanr(M.Yil,M.Toplam_Kelime); res['Spearman_Yil_ProgramUzunlugu']={'rho':float(rho.statistic),'p':float(rho.pvalue)}
rho=stats.spearmanr(M.Yil,M.Saglik_Kelime); res['Spearman_Yil_SaglikKelime']={'rho':float(rho.statistic),'p':float(rho.pvalue)}
rho=stats.spearmanr(M.Toplam_Kelime,M['Saglik_Payi_%']); res['Spearman_Uzunluk_SaglikPayi']={'rho':float(rho.statistic),'p':float(rho.pvalue)}
co=M[M.Tur_Grubu=='Koalisyon']['Saglik_Payi_%']; sp=M[M.Tur_Grubu=='Tek parti (çoğunluk)']['Saglik_Payi_%']
mw=stats.mannwhitneyu(co,sp); res['MannWhitney_Koalisyon_vs_TekParti']={'U':float(mw.statistic),'p':float(mw.pvalue),'n_koal':int(len(co)),'n_tek':int(len(sp)),'medyan_koal':float(co.median()),'medyan_tek':float(sp.median())}
# tema eğilimleri: yıl ile tema varlığı (point-biserial ~ spearman)
res['Tema_Yil_Spearman']={TLABEL[k]:{'rho':round(float(stats.spearmanr(TM.Yil,TM[k]).statistic),3),'p':round(float(stats.spearmanr(TM.Yil,TM[k]).pvalue),4)} for k in THEMES if TM[k].nunique()>1}
json.dump(res,open(f'{V}/istatistik_testleri.json','w'),ensure_ascii=False,indent=1)
# ---------------- ayırt edici terimler (log-likelihood, dönem vs diğerleri) ----------------
STOP=set(norm(w) for w in '''ve ile bir bu da de için olan olarak daha çok en gibi kadar her şekilde ise ya veya ki ne o şu bunu bunun buna bunlar bütün tüm hem ancak fakat yani yeni ayrıca olacak edilecek edilmesi edilmiştir edecek etmek olmak olduğu olduğunu olunacak olmuştur yapılacak sağlanacak bulunan bulunmaktadır kendi gerek gereken hususunda hususu hususta ait dair göre karşı arasında üzerinde önemli büyük memleket memleketimiz memleketimizin hükümet hükümetimiz hükümetimizin milletimizin milli devlet vatandaş vatandaşlarımızın sayın arkadaşlar efendiler cumhuriyet suretle surette lazım lüzumlu icap mevcut tedbir tedbirler gayret gayretle devam alınacak çalışmalar faaliyet hizmet hizmetleri hizmetlerinin sahasında alanında alanında önem verilecek getirilecek yıl yılında yılı'''.split())
def toks(s): return [w for w in re.findall(r"[a-zçğıöşü]+",s) if len(w)>2 and w not in STOP]
def stem(w): return w[:6]
H=P[P.Saglik_Paragraf].merge(M[['Hukumet_ID','Donem']],on='Hukumet_ID')
cnt=collections.defaultdict(collections.Counter); forms=collections.defaultdict(collections.Counter)
for d,txt in zip(H.Donem,H.norm):
    for w in toks(txt): cnt[d][stem(w)]+=1; forms[stem(w)][w]+=1
tot=collections.Counter(); [tot.update(c) for c in cnt.values()]
N=sum(tot.values()); rows=[]
for d in order:
    a_tot=sum(cnt[d].values()); b_tot=N-a_tot
    for s,a in cnt[d].items():
        if a<4: continue
        b=tot[s]-a; E1=a_tot*(a+b)/N; E2=b_tot*(a+b)/N
        ll=2*((a*math.log(a/E1) if a else 0)+(b*math.log(b/E2) if b else 0))
        if a/a_tot>b/max(b_tot,1): rows.append(dict(Donem=d,Kok=s,Ornek_Bicim=forms[s].most_common(1)[0][0],Donem_Frekans=a,Diger_Frekans=b,Donem_10bin=round(a/a_tot*1e4,1),Diger_10bin=round(b/b_tot*1e4,1),LL=round(ll,2)))
K=pd.DataFrame(rows).sort_values(['Donem','LL'],ascending=[True,False])
K['p<0.001']=K.LL>10.83
K.groupby('Donem').head(25).to_csv(f'{V}/donem_ayirt_edici_terimler.csv',index=False,encoding='utf-8-sig')
# ---------------- sağlık paragrafları (nitel kodlama için) ----------------
H2=P[P.Saglik_Paragraf].merge(M[['Hukumet_ID','Hukumet_No_veya_IVH_No','Resmi_Adi','Yil','Donem','Tur_Grubu']],on='Hukumet_ID')
H2['Temalar']=H2.apply(lambda x:'; '.join(TLABEL[k] for k in THEMES if x[k]>0),axis=1)
out=H2[['Hukumet_ID','Hukumet_No_veya_IVH_No','Resmi_Adi','Yil','Donem','Tur_Grubu','Paragraf_No','Kelime','Saglik_Terim','Temalar','Metin']]
with pd.ExcelWriter(f'{V}/saglik_paragraflari.xlsx') as w:
    out.to_excel(w,sheet_name='Saglik_Paragraflari',index=False)
    pd.DataFrame([(k,TLABEL[k],' | '.join(v)) for k,v in THEMES.items()],columns=['Kod','Tema','Sozluk_kaliplari']).to_excel(w,sheet_name='Kod_Kitabi',index=False)
    pd.DataFrame({'Saglik_terim_kaliplari':HEALTH}).to_excel(w,sheet_name='Saglik_Sozlugu',index=False)
# doğrulama örneklemi (tohum sabit)
random.seed(seed('on_dogrulama_ornek_1'))
pos2=P[P.Saglik_Paragraf].sample(40,random_state=seed('on_dogrulama_ornek_2'))
pos2.assign(Sinif='Sağlık (düzeltme sonrası bağımsız örneklem)')[['Hukumet_ID','Paragraf_No','Sinif','Metin']].to_csv(f'{V}/dogrulama_orneklemi_2.csv',index=False,encoding='utf-8-sig')
pos=P[P.Saglik_Paragraf].sample(40,random_state=seed('on_dogrulama_ornek_1')); neg=P[(~P.Saglik_Paragraf)&P.norm.str.contains(r'\btedavi|\bsağlıklı|\bnüfus|\bsosyal güvenlik|\bsigorta')].sample(20,random_state=seed('on_dogrulama_ornek_1'))
S=pd.concat([pos.assign(Sinif='Sağlık'),neg.assign(Sinif='Sağlık değil (zor negatif)')])[['Hukumet_ID','Paragraf_No','Sinif','Metin']]
S.to_csv(f'{V}/dogrulama_orneklemi.csv',index=False,encoding='utf-8-sig')
print(DS.to_string()); print(TS.to_string()); print(json.dumps({k:v for k,v in res.items() if k!='Tema_Yil_Spearman'},ensure_ascii=False,indent=0))
print(pres.round(0).rename(columns=lambda c:c[:3]).to_string())

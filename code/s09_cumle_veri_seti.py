"""s09 — Özgün: 09_cumle_veri_seti.py (yalnızca yollar değişti).
09_cumle_veri_seti.py — Revizyon (16.11.2026): 84 belgenin tamamı için cümle düzeyinde ortak veri seti.
Ölçütler 02_analiz.py ile aynıdır (sözlük, maske, tarım filtresi, tema sözlükleri değiştirilmemiştir).
Çıktı: veri/revizyon/belge_envanteri.csv, saglik_cumleleri.csv.gz (yalnızca sağlık cümleleri, tema isabetleriyle)"""
import os,re,pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
O=RV
import sozlukler as _soz; ns = dict(vars(_soz))
norm,mask,hsent,words,HRE,TRE,TLABEL,DROP,sentences=[ns[k] for k in ('norm','mask','hsent','words','HRE','TRE','TLABEL','DROP','sentences')]
H=pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv'); K=pd.read_csv(f'{V}/karsilastirma_korpuslari_metrikleri.csv')
P=pd.read_csv(PARAS); P=P[~P['Metin'].str.contains(DROP)]
docs=[]; rows=[]
def process(did,tur,yil,donem,paras):
    tot=0; hw=0; ns_=0; hs=0
    for pi,p in enumerate(paras):
        tot+=len(words(p)); ss=sentences(p); ns_+=len(ss)
        for si,c in enumerate(ss):
            if c in hs_set.get(pi,()): pass
        for c in hsent(p):
            n=mask(norm(c)); w=len(words(c)); hw+=w; hs+=1
            hit={k:len(r.findall(n)) for k,r in TRE.items()}
            rows.append(dict(Belge_ID=did,Tur=tur,Yil=yil,Donem=donem,Paragraf=pi+1,Cumle=c,Kelime=w,Saglik_Terim=len(HRE.findall(n)),**hit))
    return tot,hw,hs,ns_
hs_set={}
for _,h in H.iterrows():
    paras=P[P.Hukumet_ID==h.Hukumet_ID].sort_values('Paragraf_No').Metin.tolist()
    tot,hw,hs,n=process(h.Hukumet_ID,'Hükümet programı',int(h.Yil),h.Donem,paras)
    docs.append(dict(Belge_ID=h.Hukumet_ID,Tur='Hükümet programı',Ad=h.Resmi_Adi,Yil=int(h.Yil),Donem=h.Donem,Hukumet_Turu=h.Tur_Grubu,Toplam_Kelime=tot,Saglik_Cumle_Kelime=hw,Saglik_Cumle_Sayisi=hs,Cumle_Sayisi=n,Kaynak='Neziroğlu ve Yılmaz (2013) / TBMM tutanakları'))
for _,k in K.iterrows():
    paras=open(f'{TXT_COMP}/{k.ID}.txt',encoding='utf-8').read().split('\n\n')
    tur='Kalkınma planı' if k.Tur=='Kalkınma planı' else ('Yıllık program (Bakanlar Kurulu)' if k.ID=='PRES-2018-YP' else 'Cumhurbaşkanlığı yıllık programı')
    tot,hw,hs,n=process(k.ID,tur,int(k.Baslangic),'',paras)
    docs.append(dict(Belge_ID=k.ID,Tur=tur,Ad=k.Ad,Yil=int(k.Baslangic),Bitis=int(k.Bitis),Donem='',Toplam_Kelime=tot,Saglik_Cumle_Kelime=hw,Saglik_Cumle_Sayisi=hs,Cumle_Sayisi=n,Kaynak='T.C. Cumhurbaşkanlığı Strateji ve Bütçe Başkanlığı',Metin_Kaynagi=k.Metin_Kaynagi))
D=pd.DataFrame(docs); D['Saglik_Payi_%']=(D.Saglik_Cumle_Kelime/D.Toplam_Kelime*100).round(2)
S=pd.DataFrame(rows)
D.to_csv(f'{O}/belge_envanteri.csv',index=False,encoding='utf-8-sig'); S.to_csv(f'{O}/saglik_cumleleri.csv.gz',index=False,encoding='utf-8-sig')
print(D.groupby('Tur').agg(n=('Belge_ID','size'),kelime=('Toplam_Kelime','sum'),saglik_cumle=('Saglik_Cumle_Sayisi','sum')))
print('toplam belge',len(D),'toplam kelime',D.Toplam_Kelime.sum())
# eski çıktılarla tutarlılık
m=D.merge(pd.concat([H[['Hukumet_ID','Saglik_Payi_%','Toplam_Kelime']].rename(columns={'Hukumet_ID':'Belge_ID'}),K[['ID','Saglik_Payi_%','Toplam_Kelime']].rename(columns={'ID':'Belge_ID'})]),on='Belge_ID',suffixes=('','_eski'))
print('pay farkı max',(m['Saglik_Payi_%']-m['Saglik_Payi_%_eski']).abs().max(),'kelime farkı max',(m.Toplam_Kelime-m.Toplam_Kelime_eski).abs().max())

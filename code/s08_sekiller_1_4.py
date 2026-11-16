"""s08 — Özgün: 04_sekiller.py (yollar değişti; Şekil 1 başlığındaki yıl aralığı 1920–2016 olarak düzeltildi, çünkü son program 2016 tarihlidir).
04_sekiller.py — makale şekilleri (PNG 300 dpi + SVG). Veri: 09_Veri_Setleri_ve_Analiz/veri/*.csv"""
import os
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
S=FIG
os.makedirs(S,exist_ok=True)
BLUE,ORANGE,AQUA='#2a78d6','#eb6834','#1baf7a'
INK,INK2,MUTED,GRID='#0b0b0b','#52514e','#8a8984','#e6e5e1'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.edgecolor':MUTED,'axes.labelcolor':INK2,
    'xtick.color':INK2,'ytick.color':INK2,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
    'grid.color':GRID,'grid.linewidth':0.6,'axes.axisbelow':True,'axes.titlesize':10,'axes.titleweight':'bold',
    'axes.titlecolor':INK,'axes.titlelocation':'left','legend.frameon':False})
def save(fig,name):
    for ext in ('png','svg'): fig.savefig(f'{S}/{name}.{ext}',dpi=300,bbox_inches='tight',facecolor='white')
    plt.close(fig)
H=pd.read_csv(f'{V}/hukumet_saglik_metrikleri.csv'); D=pd.read_csv(f'{V}/donem_ozet.csv')
K=pd.read_csv(f'{V}/karsilastirma_korpuslari_metrikleri.csv')
BOUNDS=[(1920,1923),(1923,1946),(1946,1960),(1960,1980),(1980,2002),(2002,2018)]
SHORT=['Meclis\nhük.','Tek parti','Çok partili\ndönem','Planlı\ndönem','Neoliberal\ndönüşüm','AK Parti\n(parlamenter)']

# Şekil 1 — hükümet programlarında sağlık payı
fig,ax=plt.subplots(figsize=(7.2,3.6))
for i,(a,b) in enumerate(BOUNDS):
    if i%2: ax.axvspan(a,b,color='#f3f2ee',lw=0,zorder=0)
    m=H[H.Donem==D.Donem[i]]['Saglik_Payi_%'].mean()
    ax.hlines(m,a+0.4,b-0.4,color=INK2,lw=1.4,zorder=2)
    ax.text((a+b)/2,1.01,SHORT[i],ha='center',va='bottom',fontsize=7,color=INK2,transform=ax.get_xaxis_transform())
ax.scatter(H.Yil,H['Saglik_Payi_%'],s=26,color=BLUE,edgecolor='white',linewidth=1,zorder=3)
z=H[H['Saglik_Payi_%']==0]
ax.scatter(z.Yil,z['Saglik_Payi_%'],s=26,facecolor='white',edgecolor=BLUE,linewidth=1.2,zorder=4)
ax.set_ylim(-0.8,30); ax.set_xlim(1918,2020)
for _,r in H[(H.Toplam_Kelime<500)&(H['Saglik_Payi_%']>5)].iterrows():
    ax.annotate(f"{int(r.Toplam_Kelime)} kelime",(r.Yil,r['Saglik_Payi_%']),xytext=(7,-2),textcoords='offset points',fontsize=6.5,color=MUTED)
ax.set_ylabel('Sağlık cümlelerinin kelime payı (%)')
ax.set_title('Şekil 1. Hükümet programlarında sağlığa ayrılan metin payı, 1920–2016 (n = 63)',pad=26)
ax.text(1918.5,-7,'Nokta: hükümet programı; boş nokta: sağlık içeriği yok; yatay çizgi: dönem ortalaması; etiket: 500 kelimeden kısa ve payı %5’i aşan metin.',fontsize=7,color=MUTED,transform=ax.transData)
save(fig,'Sekil_1_hukumet_programlari_saglik_payi')

# Şekil 2 — üç belge türü
fig,ax=plt.subplots(figsize=(7.2,3.6))
ax.scatter(H.Yil,H['Saglik_Payi_%'],s=18,color=BLUE,edgecolor='white',linewidth=0.8,label='Hükümet programları (1920–2018)',zorder=3)
P=K[K.Tur=='Kalkınma planı'].dropna(subset=['Saglik_Payi_%']).sort_values('Baslangic')
for _,r in P.iterrows(): ax.hlines(r['Saglik_Payi_%'],r.Baslangic,r.Bitis+1,color=ORANGE,lw=2.4,zorder=4)
ax.plot([],[],color=ORANGE,lw=2.4,label='Kalkınma planları (plan süresi boyunca)')
Y=K[K.Tur!='Kalkınma planı'].dropna(subset=['Saglik_Payi_%']).sort_values('Baslangic')
ax.plot(Y.Baslangic,Y['Saglik_Payi_%'],color=AQUA,lw=2,marker='o',ms=4.5,mec='white',mew=0.8,label='Yıllık programlar (2018–2026)',zorder=5)
ax.set_ylim(0,12); ax.set_xlim(1918,2030)
ax.set_ylabel('Sağlık cümlelerinin kelime payı (%)')
ax.set_title('Şekil 3. Belge türlerine göre sağlık payı')
ax.text(1920,11.3,'Ölçek dışında kalan programlar: I. İVH 1920 (%25,2) ve 4. Hükümet 1925 (%27,6; 127 kelime).',fontsize=7,color=MUTED)
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.1),ncol=3,fontsize=7.5)
save(fig,'Sekil_3_belge_turleri_karsilastirma')

# Şekil 3 — dönem × tema ısı haritası
T=pd.read_csv(f'{V}/donem_tema_varlik_yuzde.csv').set_index('Donem')
cm=LinearSegmentedColormap.from_list('b',['#f5f9fe','#cde2fb','#86b6ef','#3987e5','#256abf','#104281'])
fig,ax=plt.subplots(figsize=(7.2,4.4))
ax.grid(False)
im=ax.imshow(T.T.values,cmap=cm,vmin=0,vmax=100,aspect='auto')
for (i,j),v in np.ndenumerate(T.T.values):
    ax.text(j,i,f'{v:.0f}',ha='center',va='center',fontsize=7,color='white' if v>=60 else INK)
ax.set_xticks(range(len(T)),SHORT,fontsize=7.5)
ax.set_yticks(range(T.shape[1]),T.columns,fontsize=7.5)
ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks(np.arange(-.5,len(T)),minor=True); ax.set_yticks(np.arange(-.5,T.shape[1]),minor=True)
ax.grid(which='minor',color='white',lw=2); ax.tick_params(which='minor',length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.03,pad=0.02); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
cb.set_label('Temayı içeren program oranı (%)',fontsize=7.5,color=INK2)
ax.set_title('Şekil 4. Sağlık temalarının dönemlere göre programlarda yer alma oranı (%)')
save(fig,'Sekil_4_donem_tema_isi_haritasi')

# Şekil 4 — program uzunluğu ve mutlak sağlık metni (iki panel, ortak yıl ekseni)
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.2,3.0),sharex=True)
a1.scatter(H.Yil,H.Toplam_Kelime/1000,s=16,color=BLUE,edgecolor='white',linewidth=0.8)
a1.set_title('a. Program uzunluğu (bin kelime)',fontsize=9); a1.set_ylim(bottom=0)
a2.scatter(H.Yil,H.Saglik_Cumle_Kelime,s=16,color=BLUE,edgecolor='white',linewidth=0.8)
a2.set_title('b. Sağlık cümlelerindeki kelime sayısı',fontsize=9); a2.set_ylim(bottom=0)
fig.suptitle('Şekil 2. Programlar uzadıkça sağlık metni mutlak olarak artıyor, payı artmıyor',x=0.01,ha='left',fontsize=10,fontweight='bold',color=INK,y=1.04)
save(fig,'Sekil_2_uzunluk_ve_mutlak_saglik')
print(sorted(os.listdir(S)))

"""s01 — Özgün: 00_Ortak/kod/01_metin_cikarimi.py. Değişiklik: metin, ayrı program PDF'i yerine özgün TBMM cildi/tutanağından aynı sayfa aralığıyla okunur; temizleme kuralları aynıdır.
Hükümet programı PDF'lerinden temiz metin ve paragraf korpusu çıkarır.
Çıktı: 08_Metin_Cikarimi/Hukumet_Programlari_TXT/*.txt, 08_Metin_Cikarimi/korpus_paragraflar.csv, temizleme_raporu.csv
Orijinal PDF'ler değiştirilmez."""
import os,re,json,subprocess,csv
import openpyxl
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import pandas as _pd
OUT=str(DERIVED); TXT=TXT_HP
_DOC=_pd.read_csv(DOCS).set_index('Belge_ID'); _SRC=_pd.read_csv(SRCS).set_index('Kaynak_ID')
def page_texts_for(gid):
    """Programın metni özgün TBMM cildinden/tutanağından sayfa aralığıyla çıkarılır (ayrı program PDF'iyle aynı metni verir)."""
    d=_DOC.loc[gid]; pdf=SOURCES/_SRC.loc[d.Kaynak_ID,'Goreli_Yol']
    if not pdf.exists(): sys.exit(f'Kaynak PDF yok: {pdf}')
    t=subprocess.run(['pdftotext','-layout','-f',str(int(d.PDF_Sayfa_Bas)),'-l',str(int(d.PDF_Sayfa_Bit)),str(pdf),'-'],capture_output=True).stdout.decode('utf-8','ignore')
    return t.split('\f')
os.makedirs(TXT,exist_ok=True)
wb=openpyxl.load_workbook(GOV_META); ws=wb.active
hdr=[c.value for c in ws[1]]
G=[dict(zip(hdr,r)) for r in ws.iter_rows(min_row=2,values_only=True)]
G=[g for g in G if g['Hukumet_Programi_Var_mi']=='Var']
BIRLESIK=set()
for g in G:
    if 'tek bölüm' in (g['Aciklamalar'] or ''): BIRLESIK.add(g['Hukumet_ID'])
WEIRD=set('àæŶÚ')
def is_header(l):
    s=l.strip()
    if not s: return False
    if any(ord(c)<32 and c not in '\t' for c in s): return True
    if sum(c in WEIRD for c in s)>=1 and re.search(r'[)*1t]',s) and len(s)<120 and re.search(r'[A-Z][a-z]{0,2}[A-Z]',s): return True
    if re.match(r'^\d{1,5}$',s): return True
    if re.match(r'^TBMM\s+B\s*:\s*\d+',s): return True
    if re.match(r'^\d{1,5}\s*•',s) or re.search(r'•\s*\d{1,5}$',s): return True
    if re.match(r'^(Cemal Gürsel /|.*Hükümetler, Programları ve Genel Kurul Görüşmeleri)',s) and len(s)<90: return True
    return False
SPK=re.compile(r'^\s*([A-ZÇĞİÖŞÜÂÎÛ][^—–]{1,90}?)\s*[—–]\s*(.*)$')
READER=re.compile(r'BAŞVEK[İI]L|BAŞBAKAN|Başvekil|Başbakan|Heyeti Reisi|Rıza Nur|DEVLET VEK[İI]L[İI]|Devlet Vekili|DEVLET BAŞKANI',)
def is_speaker(sp):
    sp=sp.strip()
    if len(sp)>85: return False
    letters=[c for c in sp if c.isalpha()]
    if not letters: return False
    up=sum(c.isupper() for c in letters)/len(letters)
    return up>0.6 or '(Devamla)' in sp or sp.startswith(('Reis','Başvekil','Dr. Rıza','İcra Vekilleri Heyeti Reisi')) or re.search(r'\([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\)$',sp) is not None
APPL=re.compile(r'\((?=[^()]{0,160}\))[^()]*?(alkış|Alkış|ALKIŞ|[Bb]ravo|sesleri|gürültü|kürsüye|[Gg]ülüşmeler|Soldan|Sağdan|sıralarından|Mikrofon)[^()]*\)')
def page_texts(pdf):
    t=subprocess.run(['pdftotext','-layout',pdf,'-'],capture_output=True).stdout.decode('utf-8','ignore')
    return t.split('\f')
rows=[];rep=[]
for g in G:
    gid=g['Hukumet_ID']
    pages=page_texts_for(gid); pages=[p for p in pages if p.strip()]
    last=len(pages)-1
    # build line stream with page idx
    lines=[]
    for pi,p in enumerate(pages):
        for l in p.splitlines():
            if is_header(l): continue
            lines.append((pi,l))
    started=False; stop=False; keep=False; buf=[]
    pmsur=(g['Basbakan_veya_Heyet_Baskani'] or '').split('(')[0].split()
    pmsur=pmsur[-1].upper() if pmsur else 'XXXX'
    LABEL=re.compile(r'^\s*(BAŞVEK[İI]L\b|BAŞBAKAN\b|DEVLET VEK[İI]L[İI]\b|GÜRSEL CEMAL|İcra Vekilleri Heyeti Reisi|Dr\. Rıza Nur|BAŞVEKİL)')
    INVITE=re.compile(r'(okumak üzere|takdim etmek üzere|arz edecektir|Söz Başvekil|Söz Başbakan|okuyacaktır|beyanatı\s*$|Programını arz)')
    # başlangıç noktası
    labs=[k for k,(pi,l) in enumerate(lines) if (LABEL.match(l.strip()) or re.match(r'^\s*Başvekil\s+\S.{0,60}\)\s*[—–]',l)) and not re.match(r'^\s*BAŞKAN\b',l.strip())]
    invs=[k for k,(pi,l) in enumerate(lines) if INVITE.search(l.strip())]
    inv=invs[0] if invs else None
    lab=None
    if inv is not None:
        after=[k for k in labs if inv<=k<=inv+12]
        lab=after[0] if after else None
    elif labs: lab=labs[0]
    if lab is not None: start=lab; mode='label'
    elif inv is not None: start=inv; mode='invite'
    elif labs: start=labs[0]; mode='label'
    else: start=None; mode='none'
    for k,(pi,l) in enumerate(lines):
        if stop or start is None: break
        if k<start: continue
        s=l.strip()
        if k==start:
            started=True; keep=True
            if mode=='label' and re.match(r'^\s*Başvekil\s',s):
                m=re.search(r'[—–]\s*(.*)$',s);
                if m and m.group(1): buf.append((pi,'§'+m.group(1)))
            elif mode=='label':
                m=re.search(r'\)\s*[—–-]?\s*(.*)$',s) or re.search(r'[—–]\s*(.*)$',s)
                rest=m.group(1) if m else ''
                if rest: buf.append((pi,'§'+rest))
            continue
        if mode=='invite' and len(buf)==0 and keep:
            # davet paragrafının devamını ve parantez notlarını atla
            if not re.match(r'^\s{3,}\S',l) or re.match(r'^\(.*\)?$',s) or LABEL.match(s):
                if LABEL.match(s):
                    m=re.search(r'\)\s*[—–-]?\s*(.*)$',s);
                    if m and m.group(1): buf.append((pi,'§'+m.group(1)))
                continue
        m=SPK.match(l)
        sp=m.group(1) if m else ''
        spk = bool(m) and (is_speaker(sp) or bool(LABEL.match(sp)))
        if not spk and LABEL.match(s) and len(s)<90:  # tireli olmayan etiket satırı
            keep=True; continue
        if spk:
            reader = bool(READER.search(sp)) or '(Devamla)' in sp or pmsur in sp.upper()
            if reader and not re.match(r'^\s*(BAŞKAN|REİS|Reis)\b',sp):
                keep=True; buf.append((pi,'§'+m.group(2))); continue
            if gid in BIRLESIK and pi>=last: stop=True; break
            if len(buf)>40 and re.match(r'^\s*(BAŞKAN|REİS)\b',sp) and re.search(r'(okunması bitmiştir|sunulmuştur|kapatıyorum|Bilgilerinize)',l): stop=True; break
            keep=False; continue
        if re.match(r'^\s*Kapanma\s+Saat',s): stop=True; break
        if keep: buf.append((pi,l))
    # paragraf birleştirme
    paras=[];cur=''
    for pi,l in buf:
        newp = l.startswith('§') or re.match(r'^\s{3,}\S',l) is not None
        s=l.lstrip('§').strip()
        if not s: continue
        if newp and cur: paras.append(cur); cur=''
        if cur.endswith('-') and s[:1].islower(): cur=cur[:-1]+s
        else: cur=(cur+' '+s).strip()
    if cur: paras.append(cur)
    clean=[]
    for p in paras:
        p=APPL.sub('',p); p=re.sub(r'\s{2,}',' ',p).strip()
        if len(re.findall(r'\w+',p))<3: continue
        clean.append(p)
    txt='\n\n'.join(clean)
    nwords=len(re.findall(r'\w+',txt))
    raw=sum(len(re.findall(r'\w+',p)) for p in pages)
    open(f"{TXT}/{gid}.txt",'w',encoding='utf-8').write(txt)
    for i,p in enumerate(clean):
        rows.append(dict(Hukumet_ID=gid,Paragraf_No=i+1,Metin=p,Kelime=len(re.findall(r'\w+',p))))
    rep.append(dict(Hukumet_ID=gid,Ad=g['Resmi_Adi'],Birlesik_Bolum=gid in BIRLESIK,PDF_Sayfa=len(pages),Ham_Kelime=raw,Temiz_Kelime=nwords,Oran=round(nwords/raw,3) if raw else 0,Paragraf=len(clean),Basladi=started,Baslangic_Yontemi=mode,Ilk_Paragraf=clean[0][:120] if clean else '',Son_Paragraf=clean[-1][-160:] if clean else ''))
with open(f'{OUT}/korpus_paragraflar.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(f'{OUT}/temizleme_raporu.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rep[0].keys())); w.writeheader(); w.writerows(rep)
for r in rep: print(r['Hukumet_ID'],r['PDF_Sayfa'],r['Ham_Kelime'],r['Temiz_Kelime'],r['Oran'],r['Paragraf'],'|',r['Ilk_Paragraf'][:60],'|',r['Son_Paragraf'][-70:])

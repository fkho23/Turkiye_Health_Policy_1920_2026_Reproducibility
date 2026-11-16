"""sozlukler — sağlık sözlüğü, dışlama maskesi, tarım bağlamı filtresi, cümle bölme ve 14 tema sözlüğü.
Özgün: 02_analiz.py başlık bölümü (değiştirilmeden taşındı; yalnızca yol satırları çıkarıldı)."""
import os,re,json,math,subprocess,collections,random
import pandas as pd, numpy as np
from scipy import stats
def norm(s):
    s=s.replace('I','ı').replace('İ','i').lower()
    return s.translate(str.maketrans({'â':'a','î':'i','û':'u','Â':'a','Î':'i','Û':'u','’':"'"}))
# ---------------- sözlükler ----------------
HEALTH=[r'\bsağlı(?:k(?!lı)|ğ)', r'\bsıhh?(?:at|ati|atı|ate|atin|atini|atine)\b', r'\bsıhh?[iı]\b', r'\bsıhh?iye', r'\bhıfz[ıi]s+[ıi]hha',
 r'\bhasta(?:ne|hane)', r'\bhekim', r'\btabi[bp]', r'\betibba', r'\bdoktor', r'\beczac', r'\beczane', r'\bilaç', r'\bilac',
 r'\başı(?:lar|ları|lama|lanma|sı)?\b', r'\bsalgın', r'\bbulaşıcı', r'\bsari\b', r'\bverem', r'\bsıtma', r'\bfrengi', r'\btrahom', r'\bkolera', r'\btif[oü]',
 r'\bhemşire', r'\bebe(?:ler|lik|lerin|leri)?\b', r'\bdispanser', r'\bsanatoryum', r'\bemraz', r'\btıp\b', r'\btıbb', r'\btıbbi', r'\bhastalık', r'\bmuayene', r'\bdiş hekim']
HEALTH=[h if h!=r'\bverem' else r'\bverem(?!e)' for h in HEALTH]
HEALTH+=[r'\bsa[gğ]hk(?!lı)',r'\bsaghk',r'\bsağlik(?!li)',r'\bsaglık(?!lı)']  # v4.1: eski plan PDF'lerindeki OCR yazım varyantları
HRE=re.compile('|'.join(HEALTH))
# Doğrulama örnekleminde (n=40) saptanan yanlış pozitif kalıplar eşleşmeden önce maskelenir
EXCL=re.compile(r'(tarımsal ilaç\w*|zirai ilaç\w*|ilaçlama\w*|zirai mücadele ilaç\w*|hayvan sağlığ\w*|hayvan hastalık\w*|hayvanat ve nebata arız olan hastalık\w*|bitki hastalık\w*|hastalık(?:lar)?(?:la)? ve haşere\w*|hastalık ve zararlı\w*|sıhh?[iî] (?:mesken|tesisat|ve ucuz mesken|ve ucuz|konut)\w*|tarım ilac\w*|tarım ilaç\w*|sağlıksız\w*|veteriner\w*)')
def mask(s): return EXCL.sub(' ',s)
def sentences(p): return [x for x in re.split(r'(?<=[\.\!\?;:])\s+',p) if x.strip()]
# Tarım/hayvancılık bağlamı: insan sağlığına özgü terim yoksa cümle sağlık sayılmaz (v4)
AGRI=re.compile(r'\b(hayvan|hayvancılık|zirai|ziraat|tarımsal|tarım|tohum|gübre|haşere|bitki|nebat|mahsul|ekin|çiftçi|ormancılık|balıkçılık|veteriner|zeytin|pamuk)')
HUMAN=re.compile(r'\b(insan sağlığ|halk sağlığ|hastane|hekim|doktor|hemşire|sağlık hizmet|sağlık ocağ|tedavi)')
AMBIG=re.compile(r'^(hastal|aşı|ilaç|ilac|salgın|bulaşıcı|sari|emraz|tıbb|tıp)')
def is_h(c):
    n=mask(norm(c)); ms=[m.group(0) for m in HRE.finditer(n)]
    if not ms: return False
    # tarım bağlamı yalnızca tüm eşleşmeler tarımda da anlamlı terimlerse (hastalık, aşı, ilaç...) dışlanır
    if AGRI.search(n) and not HUMAN.search(n) and all(AMBIG.match(x) for x in ms): return False
    return True
def hsent(p): return [c for c in sentences(p) if is_h(c)]
THEMES={
 'T01_Bulasici_hastalik_ve_koruyucu_saglik':[r'\bsalgın',r'\bbulaşıcı',r'\bsari\b',r'\bverem',r'\bsıtma',r'\bfrengi',r'\btrahom',r'\bkolera',r'\btif[oü]',r'\başı(?:lar|ları|lama|lanma|sı)?\b',r'\bkoruyucu (?:sağlık|hekim|hizmet)',r'\bhıfz[ıi]s+[ıi]hha',r'\bhalk sağlığ',r'\bemraz',r'\bepidemi',r'\bpandemi',r'\bcovid',r'\bbağışıklama'],
 'T02_Tedavi_hizmetleri_ve_hastaneler':[r'\bhasta(?:ne|hane)',r'\btedavi',r'\byatak',r'\bpoliklinik',r'\bşehir hastane',r'\bsanatoryum',r'\bdispanser'],
 'T03_Saglik_insan_gucu':[r'\bhekim',r'\btabi[bp]',r'\betibba',r'\bdoktor',r'\bhemşire',r'\bebe(?:ler|lik|lerin|leri)?\b',r'\bsağlık personel',r'\btıp fakülte',r'\bmütehassıs',r'\buzman hekim',r'\bsağlık memur',r'\bsağlık insan gücü'],
 'T04_Birinci_basamak_sosyallestirme_kirsal':[r'\bsosyalleştir',r'\bsosyalizasyon',r'\bsağlık ocağ',r'\bsağlık ev',r'\bbirinci basamak',r'\baile hekim',r'\bsağlık merkez',r'\btemel sağlık',r'\bköy',r'\bkırsal'],
 'T05_Finansman_ve_saglik_sigortasi':[r'\bsigorta',r'\byeşil kart',r'\bfinansman',r'\bprim\b',r'\bprimler',r'\bsosyal güvenlik',r'\bdöner sermaye',r'\bkatkı pay',r'\bödeme gücü',r'\bsağlık harcama',r'\bgeri ödeme'],
 'T06_Ozel_sektor_ve_piyasa':[r'\bözel sektör',r'\bözel hastane',r'\bözelleştir',r'\bkamu-?\s?özel',r'\bişbirliği modeli',r'\b(?:özel|hususi) teşebbüs',r'\bserbest hekim',r'\bözel sağlık',r'\bhizmet alım',r'\bsağlık piyasa'],
 'T07_Ilac_saglik_sanayii_teknoloji':[r'\bilaç',r'\bilac',r'\beczac',r'\beczane',r'\btıbbi cihaz',r'\bsağlık sanayi',r'\bbiyoteknoloj',r'\bserum',r'\başı üret',r'\bmüstahzar',r'\bedviye'],
 'T08_Ana_cocuk_sagligi_ve_nufus':[r'\bana(?: ve|-)? ?çocuk',r'\banne',r'\bçocuk sağlığ',r'\bdoğum',r'\bnüfus planlama',r'\baile planlama',r'\bbebek',r'\bgebe',r'\blohusa',r'\bdoğurganlık'],
 'T09_Sosyal_yardim_ve_dezavantajli_gruplar':[r'\bmuavenet',r'\bsosyal yardım',r'\byoksul',r'\bfakir',r'\bengelli',r'\bözürlü',r'\bsakat',r'\byaşlı',r'\bkimsesiz',r'\bdüşkün',r'\bbakım(?:evi|evleri| hizmet| ve rehabilitasyon)',r'\bevde bakım',r'\bhimaye',r'\bmuhtaç',r'\bücretsiz'],
 'T10_Reform_yonetisim_kalite':[r'\breform',r'\byeniden yapılan',r'\bverimlilik',r'\bperformans',r'\bkalite',r'\bakreditasyon',r'\bhasta hak',r'\bmemnuniyet',r'\bdönüşüm',r'\bteşkilat',r'\bkoordinasyon',r'\bdenetim'],
 'T11_Dijital_saglik_ve_bilgi_sistemleri':[r'\be-sağlık',r'\bbilgi sistem',r'\belektronik',r'\bdijital',r'\btele-?tıp',r'\bveri taban',r'\bsağlık-?net',r'\be-nabız',r'\bbilişim'],
 'T12_Saglik_turizmi':[r'\bsağlık turizm',r'\btermal',r'\bmedikal turizm'],
 'T13_Saglikli_yasam_ve_kronik_hastaliklar':[r'\bobezite',r'\bsigara',r'\btütün',r'\bkronik',r'\bbeslenme',r'\balkol',r'\buyuşturucu',r'\bbağımlılık',r'\bkanser',r'\bsağlıklı yaşam',r'\bhareketli',r'\bdiyabet'],
 'T14_Acil_afet_ve_ambulans':[r'\bacil\b',r'\bacil sağlık',r'\bambulans',r'\bafet',r'\b112\b'],
}
TRE={k:re.compile('|'.join(v)) for k,v in THEMES.items()}
TLABEL={'T01_Bulasici_hastalik_ve_koruyucu_saglik':'Bulaşıcı hastalık ve koruyucu sağlık','T02_Tedavi_hizmetleri_ve_hastaneler':'Tedavi hizmetleri ve hastaneler','T03_Saglik_insan_gucu':'Sağlık insan gücü','T04_Birinci_basamak_sosyallestirme_kirsal':'Birinci basamak, sosyalleştirme, kırsal','T05_Finansman_ve_saglik_sigortasi':'Finansman ve sağlık sigortası','T06_Ozel_sektor_ve_piyasa':'Özel sektör ve piyasa','T07_Ilac_saglik_sanayii_teknoloji':'İlaç, sağlık sanayii, teknoloji','T08_Ana_cocuk_sagligi_ve_nufus':'Ana-çocuk sağlığı ve nüfus','T09_Sosyal_yardim_ve_dezavantajli_gruplar':'Sosyal yardım ve dezavantajlı gruplar','T10_Reform_yonetisim_kalite':'Reform, yönetişim, kalite','T11_Dijital_saglik_ve_bilgi_sistemleri':'Dijital sağlık ve bilgi sistemleri','T12_Saglik_turizmi':'Sağlık turizmi','T13_Saglikli_yasam_ve_kronik_hastaliklar':'Sağlıklı yaşam ve kronik hastalıklar','T14_Acil_afet_ve_ambulans':'Acil, afet, ambulans'}
DROP=re.compile(r'(Kapanma,?\s*Saat|birleşimi kapatıyorum|Meclis Grupu Başkanı\s*$|Muvafakat ediyoruz)',re.I)
def words(s): return re.findall(r"[^\W\d_]+",s)

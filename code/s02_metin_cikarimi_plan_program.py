"""s02 — Kalkınma planları (1–12) ve yıllık programlar (2018 BK, 2019–2026 CB) için metin çıkarımı.
Özgün: 09_Veri_Setleri_ve_Analiz/Makale_1_Hukumet_Programlari/kod/03_karsilastirma_korpuslari.py (metin çıkarım bölümü; mantık değiştirilmedi).
Girdi : sources/<Goreli_Yol> (kaynak_dosyalar.csv), 9. Plan için <derived>/OCR/DEVPLAN_09_..._OCR.txt (s02b ile üretilir)
Çıktı : <derived>/Karsilastirma_TXT/<Belge_ID>.txt
Kural : pdftotext (düzen korunmadan, varsayılan kip); 'õ' sayısı > 1000 ise õ→ı yazı tipi onarımı; satır sonu tireleri birleştirilir;
        boş satırlarla ayrılan bloklar paragraf sayılır; 5 kelimeden kısa paragraflar atılır."""
import os, re, sys, subprocess
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from sozlukler import words

os.makedirs(TXT_COMP, exist_ok=True)
D = pd.read_csv(DOCS); S = pd.read_csv(SRCS).set_index('Kaynak_ID')
OCR_FILE = os.path.join(OCR_DIR, 'DEVPLAN_09_Dokuzuncu_Kalkinma_Plani_2007_2013_OCR.txt')
rep = []
for _, d in D[D.Tur != 'Hükümet programı'].iterrows():
    if d.Belge_ID == 'DEVPLAN-09':
        if not os.path.exists(OCR_FILE):
            sys.exit('9. Plan OCR metni yok: önce s02b_ocr_plan9.py çalıştırılmalı veya --derived ile hazır metin verilmeli.')
        t = open(OCR_FILE, encoding='utf-8', errors='ignore').read()
    else:
        pdf = SOURCES / S.loc[d.Kaynak_ID, 'Goreli_Yol']
        if not pdf.exists():
            sys.exit(f'Kaynak PDF yok: {pdf} (s00_kaynaklari_indir.py ile indirin)')
        t = subprocess.run(['pdftotext', str(pdf), '-'], capture_output=True).stdout.decode('utf-8', 'ignore')
    onarim = t.count('õ') > 1000
    if onarim: t = t.replace('õ', 'ı')
    t = re.sub(r'-\n(?=[a-zçğıöşü])', '', t); t = t.replace('\f', '\n')
    paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', t)]
    paras = [p for p in paras if len(words(p)) >= 5]
    open(os.path.join(TXT_COMP, f'{d.Belge_ID}.txt'), 'w', encoding='utf-8').write('\n\n'.join(paras))
    rep.append(dict(Belge_ID=d.Belge_ID, Paragraf=len(paras), Kelime=sum(len(words(p)) for p in paras), Font_onarimi=onarim))
pd.DataFrame(rep).to_csv(os.path.join(str(DERIVED), 'karsilastirma_cikarim_raporu.csv'), index=False, encoding='utf-8-sig')
print(pd.DataFrame(rep).to_string())

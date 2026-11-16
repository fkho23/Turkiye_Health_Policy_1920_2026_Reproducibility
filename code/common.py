"""Ortak yollar ve parametreler.

Tüm yollar paket köküne göredir; bilgisayara özgü yol yoktur. Ortam değişkenleriyle değiştirilebilir:
  REPRO_OUT      çıktı klasörü                    (varsayılan: <paket>/outputs)
  REPRO_SOURCES  özgün kaynak PDF klasörü          (varsayılan: <paket>/sources)
  REPRO_DERIVED  türetilmiş (çıkarılmış) metinler   (varsayılan: <REPRO_OUT>/derived_text)
run_all.py bu değişkenleri komut satırı seçeneklerine göre ayarlar.
"""
import os
import json
import pathlib

PKG = pathlib.Path(__file__).resolve().parent.parent
CFG = json.load(open(PKG / 'config' / 'params.json', encoding='utf-8'))
OUT = pathlib.Path(os.environ.get('REPRO_OUT', PKG / 'outputs')).resolve()
SOURCES = pathlib.Path(os.environ.get('REPRO_SOURCES', PKG / 'sources')).resolve()
DERIVED = pathlib.Path(os.environ.get('REPRO_DERIVED', OUT / 'derived_text')).resolve()
INV = PKG / 'inventory'

V = str(OUT / 'veri')                    # analiz veri ve test çıktıları
RV = str(OUT / 'veri' / 'revizyon')      # revizyon (v5) analizleri
FIG = str(OUT / 'sekiller')              # şekiller
TAB = str(OUT / 'tablolar')              # makale tabloları
VAL = str(OUT / 'dogrulama')             # doğrulama formları
for _d in (V, RV, FIG, TAB, VAL):
    os.makedirs(_d, exist_ok=True)

PARAS = str(DERIVED / 'korpus_paragraflar.csv')     # hükümet programı paragraf korpusu
TXT_HP = str(DERIVED / 'Hukumet_Programlari_TXT')    # hükümet programı düz metinleri
TXT_COMP = str(DERIVED / 'Karsilastirma_TXT')        # kalkınma planı + yıllık program metinleri
OCR_DIR = str(DERIVED / 'OCR')                       # 9. Plan OCR metni
GOV_META = str(INV / 'Hukumet_Listesi.xlsx')         # hükümet üst verisi (dönem, tür, sayfa)
DOCS = str(INV / 'analiz_belgeleri.csv')             # 84 analiz belgesi
SRCS = str(INV / 'kaynak_dosyalar.csv')              # kaynak PDF dosyaları (URL, SHA-256)


def seed(name):
    return CFG['seeds'][name]

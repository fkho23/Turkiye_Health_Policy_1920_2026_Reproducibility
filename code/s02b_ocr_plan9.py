"""s02b — 9. Kalkınma Planı (taranmış görüntü) için OCR.
Ayarlar (config/params.json -> ocr): pdftoppm 300 dpi gri tonlama, Tesseract 4.1.1 'tur' modeli, sayfa sayfa.
Tesseract her sayfanın sonuna form feed (\\f) ekler; sayfalar bu çıktıların doğrudan birleştirilmesiyle oluşturulur.
UYARI: OCR çıktısı Tesseract/Leptonica sürümüne ve dil modeline duyarlıdır. Başka bir sürümle üretilen metin
birkaç karakter farklı olabilir; analizdeki etkisi s15 doğrulama raporunda gösterilir.
Çıktı: <derived>/OCR/DEVPLAN_09_Dokuzuncu_Kalkinma_Plani_2007_2013_OCR.txt"""
import os, sys, subprocess, tempfile, glob
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

os.makedirs(OCR_DIR, exist_ok=True)
S = pd.read_csv(SRCS).set_index('Kaynak_ID')
pdf = SOURCES / S.loc['DEVPLAN-09', 'Goreli_Yol']
if not pdf.exists(): sys.exit(f'Kaynak PDF yok: {pdf}')
o = CFG['ocr']
n = int([l for l in subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout.splitlines() if l.startswith('Pages')][0].split()[-1])
import argparse, time
ap = argparse.ArgumentParser(); ap.add_argument('--zaman-siniri', type=float, default=0, help='saniye; >0 ise süre dolunca durur, yeniden çalıştırınca kaldığı sayfadan devam eder')
arg = ap.parse_args(); t0 = time.time()
langs = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True)
if o['dil'] not in (langs.stdout + langs.stderr).split(): sys.exit(f"Tesseract '{o['dil']}' dil modeli bulunamadı. README > OCR bölümüne bakın.")
cache = os.path.join(OCR_DIR, '_sayfalar_plan9'); os.makedirs(cache, exist_ok=True)   # kesintiye dayanıklı sayfa önbelleği
with tempfile.TemporaryDirectory() as td:
    for i in range(1, n + 1):
        cf = os.path.join(cache, f'p{i:04d}.txt')
        if os.path.exists(cf): continue
        if arg.zaman_siniri and time.time() - t0 > arg.zaman_siniri:
            print(f'Süre sınırı: {i - 1}/{n} sayfa hazır; yeniden çalıştırın.'); sys.exit(3)
        subprocess.run(['pdftoppm', '-r', str(o['dpi']), '-gray', '-f', str(i), '-l', str(i), '-png', str(pdf), f'{td}/p'], check=True)
        img = sorted(glob.glob(f'{td}/p-*.png'))[0]
        r = subprocess.run(['tesseract', img, 'stdout', '-l', o['dil']], capture_output=True)
        txt = r.stdout.decode('utf-8', 'ignore')
        if r.returncode != 0 or b'Failed loading' in r.stderr or b'Could not initialize' in r.stderr:   # dil modeli yoksa tesseract boş çıktı verir: sessizce devam etme
            sys.exit(f'Tesseract sayfa {i} için başarısız (dönüş {r.returncode}). Türkçe model kurulu mu? (tesseract --list-langs; '
                     f'gerekirse TESSDATA_PREFIX). stderr: {r.stderr.decode("utf-8", "ignore")[-300:]}')
        os.remove(img)
        open(cf + '.tmp', 'w', encoding='utf-8').write(txt); os.replace(cf + '.tmp', cf)
        print(f'{i}/{n}', flush=True)
parts = [open(os.path.join(cache, f'p{i:04d}.txt'), encoding='utf-8').read() for i in range(1, n + 1)]
open(os.path.join(OCR_DIR, 'DEVPLAN_09_Dokuzuncu_Kalkinma_Plani_2007_2013_OCR.txt'), 'w', encoding='utf-8').write(''.join(parts))
print('\nOCR tamam')

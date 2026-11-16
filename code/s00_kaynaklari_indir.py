"""s00 — Özgün kaynak PDF'lerini resmî adreslerinden indirir ve SHA-256 ile doğrular.
Kullanım:  python code/s00_kaynaklari_indir.py            # eksikleri indir + hepsini doğrula
           python code/s00_kaynaklari_indir.py --dogrula  # yalnızca doğrula (indirme yok)
Dosyalar sources/<Goreli_Yol> konumuna yazılır. Var olan ve özeti tutan dosyanın üzerine yazılmaz.
Kaynak kurumlar dosyayı değiştirirse özet tutmaz; bu durumda dosya korunur ve rapora 'ÖZET FARKLI' yazılır."""
import os, sys, hashlib, urllib.request, shutil
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

UA = 'Mozilla/5.0 (X11; Linux x86_64) research-reproducibility-script'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def indir(url, hedef):
    tmp = str(hedef) + '.indiriliyor'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, 'wb') as f: shutil.copyfileobj(r, f)
    if open(tmp, 'rb').read(4) != b'%PDF': os.remove(tmp); raise ValueError('PDF değil')
    os.replace(tmp, hedef)


S = pd.read_csv(SRCS); yalniz_dogrula = '--dogrula' in sys.argv; rap = []
for _, s in S.iterrows():
    p = SOURCES / s.Goreli_Yol; p.parent.mkdir(parents=True, exist_ok=True); durum = ''
    if not p.exists() and not yalniz_dogrula:
        for u in [s.URL, s.Alternatif_URL]:
            if isinstance(u, str) and u.startswith('http'):
                try: indir(u, p); durum = 'İNDİRİLDİ '; break
                except Exception as e: durum = f'HATA({type(e).__name__}) '
    if p.exists():
        durum += 'ÖZET TUTUYOR' if sha(p) == s.SHA256 else 'ÖZET FARKLI'
    else:
        durum += 'YOK'
    rap.append(dict(Kaynak_ID=s.Kaynak_ID, Durum=durum, Yol=s.Goreli_Yol)); print(s.Kaynak_ID, durum)
R_ = pd.DataFrame(rap); os.makedirs(str(OUT), exist_ok=True)
R_.to_csv(OUT / 'kaynak_dogrulama_raporu.csv', index=False, encoding='utf-8-sig')
ok = R_.Durum.str.endswith('ÖZET TUTUYOR').sum(); print(f'{ok}/{len(R_)} kaynak dosya doğrulandı.')
sys.exit(0 if ok == len(R_) else 1)

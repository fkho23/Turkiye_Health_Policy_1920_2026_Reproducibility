# Türkiye'de Sağlık Politikası Belgeleri, 1920–2026 — Tekrarlanabilirlik Paketi (v1.0.0)

Bu depo, *“Türkiye'de Sağlık Sisteminin Politika Belgelerine Yansıyan Kurumsal ve Yönetsel Dönüşümü (1920–2026): Hükümet Programları, Kalkınma Planları ve Yıllık Programların Nicel Metin Analizi”* başlıklı makaledeki bütün hesaplamalı analizleri yeniden üretmek için gereken kodu, parametreleri, belge envanterini ve beklenen çıktıları içerir.

*English summary:* Code, parameters, source inventory (official URLs + SHA-256) and expected outputs for fully reproducing the quantitative text analysis of 84 Turkish policy documents (63 government programmes, 12 development plans, 9 annual programmes; 1920–2026). Source PDFs are **not** redistributed; `s00` downloads them from the official sites and verifies their SHA-256 hashes. One command (`python run_all.py --kaynaklar sources`) runs the whole pipeline and compares 492 reported values with the article.

---

## 1. Ne yeniden üretilir?

| Aşama | Betik | Çıktı |
|---|---|---|
| Kaynak PDF indirme ve SHA-256 doğrulama | `s00_kaynaklari_indir.py` | `kaynak_dogrulama_raporu.csv` |
| Hükümet programı metinleri (TBMM ciltleri ve tutanaklar, sayfa aralığıyla) | `s01_metin_cikarimi_hukumet_programlari.py` | `derived_text/` |
| 9. Kalkınma Planı OCR (taranmış belge) | `s02b_ocr_plan9.py` | `derived_text/OCR/` |
| Plan ve yıllık program metinleri | `s02_metin_cikarimi_plan_program.py` | `derived_text/` |
| Sağlık cümlesi tespiti, dönem/tür/tema analizleri, LL | `s03_analiz_hukumet_programlari.py` | `veri/` |
| Karşılaştırma korpusu metrikleri | `s04_karsilastirma_metrikleri.py` | `veri/` |
| Sağlamlık testleri, program–plan eşleştirme | `s05_saglamlik_testleri.py` | `veri/` |
| Etki büyüklüğü, bootstrap, Holm, basıklık | `s06_ek_testler.py` | `veri/ek_testler.json` |
| 2018–2026 yıllık programlar | `s07_cumhurbaskanligi_donemi.py` | `veri/` |
| Şekil 1–4 | `s08_sekiller_1_4.py` | `sekiller/` |
| Cümle düzeyi veri seti | `s09_cumle_veri_seti.py` | `veri/revizyon/` |
| Revizyon analizleri (Tablo 5, plan düzeyi Wilcoxon, kesin permütasyon, Holm + uzunluk denetimi, L-basıklık, DSÖ yapı taşları, yalnızca sağlık cümlelerinde LL) | `s10_revizyon_analizleri.py` | `veri/revizyon/` |
| Şekil 5 (DSÖ yapı taşları) | `s11_who_sekil.py` | `sekiller/` |
| Terim sayımları | `s16_terim_sayimlari.py` | `veri/revizyon/` |
| İki ayrı kör değerlendirici formu (160 + 266 kayıt) | `s12_dogrulama_formlari.py` | `dogrulama/` |
| Makale tabloları ve tablo/şekil → veri/kod eşleştirmesi | `s14_makale_tablolari.py` | `tablolar/` |
| Makaledeki 492 değerle otomatik karşılaştırma | `s15_makale_ile_karsilastir.py` | `DOGRULAMA_RAPORU.md` |
| Kodlayıcılar arası uyum (formlar doldurulduktan sonra) | `s13_kodlayici_uyumu.py` | `dogrulama/uyum_*.csv` |

Her tablo ve şeklin hangi betik ve veri dosyasından üretildiği: `expected/tablolar/Tablo_Sekil_Eslestirme.csv`.

## 2. Kurulum

Sınandığı ortam (makaledeki sonuçlar): Ubuntu 22.04, Python 3.10.12, poppler-utils 22.02.0, tesseract 4.1.1.

```bash
# sistem araçları (Debian/Ubuntu)
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-tur
# Python paketleri
python -m pip install -r requirements.txt
```

Windows/macOS: poppler ve tesseract'ı kurup `pdftotext`, `pdfinfo`, `pdftoppm`, `tesseract` komutlarının PATH'te olduğundan emin olun. Bütün yollar pakete göreli tanımlıdır; hiçbir betik belirli bir bilgisayara özgü yol içermez.

## 3. Çalıştırma

```bash
# 1) Kaynak PDF'leri resmî adreslerinden indir ve SHA-256 ile doğrula (34 dosya, yaklaşık 930 MB)
python code/s00_kaynaklari_indir.py

# 2) Bütün hattı temiz bir çıktı klasörüne çalıştır (9. Plan için OCR dahil)
python run_all.py --kaynaklar sources --ocr calistir --cikti outputs
```

Seçenekler:

| Seçenek | Anlamı |
|---|---|
| `--kaynaklar DIR` | Kaynak PDF klasörü (`inventory/kaynak_dosyalar.csv` içindeki `Goreli_Yol` yapısıyla) |
| `--turetilmis DIR` | Metin çıkarımını atla, hazır türetilmiş metinleri kullan |
| `--ocr calistir` | 9. Plan OCR'ını baştan yap (122 sayfa; ~15–25 dk). Kesilirse yeniden çalıştırınca kaldığı sayfadan sürer |
| `--ocr hazir --ocr-metni FILE` | Elinizde bulunan OCR metnini kullan |
| `--form1 F1.xlsx --form2 F2.xlsx` | Doldurulmuş kör formlarla kodlayıcı uyumunu hesapla |

Çalıştırma sonunda `outputs/ortam.json` (sürümler, parametreler, seed'ler), `outputs/gunluk/*.log` (her adımın çıktısı), `outputs/calistirma_gunlugu.json` (süreler, dönüş kodları) ve `outputs/DOGRULAMA_RAPORU.md` yazılır.

## 4. Parametreler ve rastgelelik

Bütün parametreler `config/params.json` içindedir: seed'ler (42, 7, 2026), bootstrap tekrar sayıları (5.000), L-basıklık Monte Carlo tekrarı (20.000), Holm aileleri, cümle bölme düzenli ifadesi, OCR ayarları (300 dpi, gri tonlama, `tur`), çıkarım kuralları ve kapsam (yürürlük ≤ 2026). `PYTHONHASHSEED=0` `run_all.py` tarafından ayarlanır.

## 5. Beklenen sonuçlar

`expected/` klasörü, bu paketin temiz bir klasörde çalıştırılmasıyla elde edilen çıktıları içerir: `veri/` (analiz veri setleri), `tablolar/` (makale tabloları ve ek tablolar), `sekiller/` (PNG + SVG), `dogrulama_formlari/` (boş kör formlar) ve `DOGRULAMA_RAPORU.md`.

Son doğrulama (16.11.2026; kaynak PDF'lerden temiz klasöre, özgün 9. Plan OCR metniyle): makalede raporlanan **492 sayısal değerin 492'si** yeniden üretildi. Bunların 14'ü ara dosyalarda 3–4 ondalıkla saklanan değerlerin tam yarım sınırında görünmesinden kaynaklanan yuvarlama sınırı durumlarıdır (ör. H = 7,2447 → makalede 7,24). Arşivdeki 32 analiz veri dosyası yeniden üretilen dosyalarla içerik düzeyinde aynıdır.

## 6. OCR hakkında (duyarlılık)

9. Kalkınma Planı'nın resmî PDF'i taranmış görüntüdür. Makaledeki sonuçlar arşivdeki özgün OCR metnine dayanır (SHA-256 `38be23a5…`, `inventory/turetilmis_metin_ozetleri.csv`). Bu metni üreten Tesseract dil modelinin tam sürümü kayıt altına alınmamıştır. `s02b` ile Tesseract 4.1.1 ve Ubuntu 22.04 `tesseract-ocr-tur` (1:4.00~git30-7274cfa-1.1, model MD5 `c64b41a5…`) kullanılarak yapılan yeni OCR bayt düzeyinde aynı metni vermez (`c563b4d7…`).

Etkisi sınanmıştır (`expected/ocr_duyarlilik/`): yeni OCR ile 492 değerin 483'ü aynı kalır. Değişen 9 değerin tamamı 9. Plan OCR metnindeki karakter farklarından kaynaklanır:
* 9. Plan kelime sayısı 36.566 → 36.279; sağlık payı %4,84 → %4,67.
* Plan düzeyi Wilcoxon p 0,16 → 0,154; 34 eşleşmede p 0,014 → 0,015.
* Tablo 9'da 7–9. Plan satırındaki DSÖ paylarında ±0,3 puan değişim; bir tema sayımında 37 → 36.

Hiçbir anlamlılık kararı ve yorum değişmez. Makaledeki değerleri birebir üretmek için özgün OCR metni `--ocr hazir --ocr-metni` ile verilmelidir. Bu metin, yeniden dağıtım gerekçesiyle depoda yoktur (bkz. `docs/`). Türkçe model kurulu değilse `s02b` sessizce boş çıktı üretmez, hata vererek durur. Kesilen OCR kaldığı sayfadan sürer.

## 7. İnsan doğrulaması (henüz yapılmadı)

Sözlük tabanlı tespitin bağımsız insan doğrulaması **henüz yapılmamıştır**; bu depo hiçbir kodlayıcı uyumu, kappa veya doğrulama oranı içermez.

* `expected/dogrulama_formlari/Degerlendirici_1_Kor_Form.xlsx` ve `Degerlendirici_2_Kor_Form.xlsx`: aynı 160 (A: sağlık tespiti) + 266 (B: tema ve DSÖ yapı taşı) kayıt, farklı sıralarda. Her kayıtta benzersiz `Kayit_ID`, kararlı cümle anahtarı, belge adı, türü ve tarihi, kaynak dosya, PDF sayfası, basılı sayfa (TBMM ciltleri), özgün cümle ve bağlamı vardır. Formlarda otomatik karar veya başka değerlendiricinin kararı **yoktur**.
* Sözlük kararlarını içeren anahtar dosya (`_ANAHTAR_..._GONDERMEYIN.xlsx`) değerlendiricilerin görmemesi için depoya konmamıştır; `s12` ile yeniden üretilir.
* Formlar doldurulduğunda: `python code/s13_kodlayici_uyumu.py --d1 F1.xlsx --d2 F2.xlsx [--uzlasi U.xlsx]` → Cohen's κ, yüzde uyum, sözlüğün kesinlik/duyarlılık/F1 değerleri (ağırlıklı ve ağırlıksız).
* `validation/on_dogrulama_arsivi/`: makalenin Tablo 2'sindeki ön denetimde kullanılan örneklemler (seed 42 ve 7). Bu ön denetim yapay zekâ destekli tek değerlendirici tarafından yapılmış, kararları kayıt altına alınmamıştır; bu nedenle **hesaplamalı olarak yeniden üretilemez** ve bağımsız insan doğrulaması yerine geçmez.

## 8. Veri ve kod erişilebilirliği, yeniden dağıtım

`docs/VERI_VE_KOD_ERISILEBILIRLIGI.md` dosyasına bakınız. Özetle: kaynak belgeler TBMM, Strateji ve Bütçe Başkanlığı ve Cumhurbaşkanlığı'nın resmî yayınlarıdır. Kaynak PDF'ler ve tam metinler depoya konmamış, resmî bağlantıları ve SHA-256 özetleri verilmiştir. Kod MIT, veri ve belgeler CC BY 4.0 lisanslıdır.

## 9. Atıf

`CITATION.cff` dosyasına bakınız. Kalıcı DOI, bu sürümün Zenodo'da arşivlenmesiyle verilir.

## 10. Dizin yapısı

```
run_all.py              tek komutla tüm hat
requirements.txt        sabitlenmiş Python sürümleri
config/params.json      seed'ler ve bütün parametreler
code/                   s00–s16 betikleri, common.py, sozlukler.py (14 tema sözlüğü)
inventory/              84 analiz belgesi, 34 kaynak dosya (URL + SHA-256), hükümet listesi
validation/             ön doğrulama örneklemleri (arşiv)
expected/               beklenen çıktılar (veri, tablolar, şekiller, boş kör formlar, doğrulama raporu)
docs/                   erişilebilirlik ve yeniden dağıtım notu, denetim raporu
sources/                (boş) s00 kaynak PDF'leri buraya indirir
```

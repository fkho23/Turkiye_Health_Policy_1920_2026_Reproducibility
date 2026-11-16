# Son tekrarlanabilirlik denetimi (16.11.2026)

Denetim, paketin kaynak PDF'lerden başlayarak temiz bir çıktı klasörüne çalıştırılmasıyla yapılmıştır (Ubuntu 22.04, Python 3.10.12, poppler 22.02.0, tesseract 4.1.1). Korpus (84 belge), 14 tema ve altı DSÖ yapı taşı değiştirilmemiştir.

## A. Tam olarak yeniden üretilen sonuçlar

| Kontrol | Sonuç |
|---|---|
| 34 kaynak PDF'in SHA-256 doğrulaması | 34/34 özet tutuyor |
| Hükümet programı metinlerinin özgün cilt sayfalarından çıkarımı | özgün analizdeki türetilmiş metinlerle bayt düzeyinde aynı |
| Makaledeki sayısal değerler (Tablo 1, 3–9, Ek Tablo E1–E3, Şekil 1–5 verileri ve metindeki istatistikler) | **492/492** (14'ü yuvarlama sınırında; ara dosyalardaki 3–4 ondalıklı saklamadan kaynaklanır, yuvarlanmamış değerlerle tutarlıdır) |
| Arşivdeki 32 analiz veri dosyası (`veri/`, `veri/revizyon/`) | 30'u bayt düzeyinde, 2'si (`.csv.gz`, `.xlsx`) içerik düzeyinde aynı. Fark yalnızca dosya kapsayıcısının zaman damgası |
| Ön doğrulama örneklemleri (`dogrulama_orneklemi.csv`, `dogrulama_orneklemi_2.csv`; seed 42 ve 7) | kayıtlar arşivle aynı |
| Kesin permütasyon, bootstrap, Monte Carlo (sabit seed) | aynı değerler |

## B. Denetimde bulunup düzeltilen sorunlar

1. **Makale Tablo 6 (ayırt edici terimler)** v3 analizinden kalmış eski LL değerlerini taşıyordu. Bu değerler v4 sağlık sözlüğü güncellemesinden önceye aittir (`_onceki_surum_v3/veri/donem_ayirt_edici_terimler.csv`). Güncel kod ve arşivin güncel çıktısı birbiriyle aynıdır; makaledeki tablo ve ilgili cümle güncel değerlerle düzeltilmiştir. Örneğin 1923–1946'da “fennî” terimi artık eşik üstünde değildir. Örüntü korunmuştur: erken dönemde sıhhiye/sıhhat/mücadele, planlı dönemde ilaç/sanayi/tedavi, 2002–2018'de icraat dili.
2. **Kör formlarda sayfa numarası:** 8. Plan'ın PDF metnindeki yazı tipi hatası (õ→ı) sayfa aramasında onarılmadığı için 7 kayıtta sayfa “bulunamadı” idi. Onarıldı; 426 kaydın tamamında PDF sayfası vardır. 9. Plan OCR metninde sayfa ayırıcısının (`\f\f`) yanlış okunması da düzeltildi.
3. **OCR betiği:** Türkçe dil modeli yoksa sessizce boş metin üretiyordu; artık hata vererek durur ve kesintide kaldığı sayfadan sürer.
4. **Karşılaştırma betiği:** kayan nokta yuvarlamasıyla yarım sınırındaki değerleri yanlışlıkla “farklı” sayıyordu; düzeltildi.

## C. Eksik kalan / tam yeniden üretilemeyen öğeler

| Öğe | Durum | Gerekçe |
|---|---|---|
| Tablo 2 (ön denetim kesinlikleri) | **Hesaplamalı olarak yeniden üretilemez** | Ön denetim yapay zekâ destekli tek değerlendirici tarafından yapılmış, kayıt düzeyinde kararlar saklanmamıştır. Kararlar geriye dönük olarak oluşturulmamıştır. Örneklemler yeniden üretilebilir |
| 9. Plan OCR metni | Baştan OCR ile bayt düzeyinde aynı değil | Özgün OCR'daki dil modelinin sürümü kaydedilmemiş. Yeniden OCR ile 492 değerin 483'ü aynı kalır; değişen 9 değer küçük ve hiçbir yorumu değiştirmiyor (`expected/ocr_duyarlilik/`) |
| Kaynak PDF'ler ve tam metinler | Depoda yok | Açık yeniden dağıtım izni yok. Bağlantı ve SHA-256 verildi; kurumlar dosyayı değiştirirse `s00` bunu raporlar |
| Şekil dosyaları (PNG/SVG) | Görsel olarak aynı, bayt düzeyinde karşılaştırılmadı | Matplotlib dosyaya zaman damgası ve yazı tipi önbelleği bilgisi yazar. Şekillerin dayandığı veriler aynıdır |

## D. İnsan doğrulaması bekleyen adımlar

Aşağıdakiler **yapılmamıştır**. Pakette bunlara ilişkin hiçbir sonuç yoktur ve uydurulmamıştır:

1. İki bağımsız insan değerlendiricinin `Degerlendirici_1_Kor_Form.xlsx` ve `Degerlendirici_2_Kor_Form.xlsx` formlarını birbirinden habersiz doldurması (A: 160 kayıt sağlık tespiti; B: 266 kayıt tema ve DSÖ yapı taşı).
2. `s13_kodlayici_uyumu.py` ile Cohen's κ, yüzde uyum, sözlüğün kesinlik/duyarlılık/F1 değerlerinin hesaplanması.
3. Anlaşmazlıkların uzlaşı turu ve uzlaşı dosyasıyla sözlük performansının yeniden hesaplanması (`--uzlasi`).
4. Bu sonuçlar elde edildiğinde makalenin 3.4 bölümünün ve Tablo 2'nin güncellenmesi ve paketin yeni sürümünün (v1.1.0) yayımlanması.

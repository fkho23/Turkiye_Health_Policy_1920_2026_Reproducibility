# Veri ve kod erişilebilirliği / yeniden dağıtım notu

## Erişilebilirlik beyanı (makale için)

Belge envanteri (resmî bağlantılar ve SHA-256 özetleri), sözlükler, kod kitabı, DSÖ eşleştirme matrisi, belge, cümle ve tema düzeyindeki veri setleri, analiz kodları, parametre ve seed kayıtları, beklenen çıktılar, sınıflandırma kararları, GitHub'da açık bir depo olarak yayımlanmış ve Zenodo'da kalıcı DOI ile arşivlenmiştir. Bütün analizler tek komutla (`run_all.py`) yeniden üretilebilir. Kaynak belgeler kurumlarının resmî yayınları olduğu için pakete eklenmemiş, resmî erişim adresleri ve SHA-256 özetleriyle tanımlanmıştır. Kod MIT, türetilmiş veri ve belgeler CC BY 4.0 lisanslıdır.

## Kaynak belgeler neden pakette yok?

| Kaynak | Yayımlayan | Pakette | Gerekçe |
|---|---|---|---|
| TBMM *Hükümetler – Programları ve Genel Kurul Görüşmeleri* (Cilt 1–10) | TBMM Kütüphane ve Arşiv Hizmetleri | Hayır | Derleyici emeği içeren yayın; açık lisansla yeniden dağıtım izni bulunamadı |
| TBMM Genel Kurul tutanakları (62., 64., 65. Hükümet) | TBMM | Hayır | Resmî bağlantı yeterli; büyük dosyalar |
| 1.–12. Kalkınma Planları, yıllık programlar | Strateji ve Bütçe Başkanlığı / Cumhurbaşkanlığı | Hayır | Açık yeniden dağıtım lisansı belirtilmemiş |

Bu nedenle `inventory/kaynak_dosyalar.csv` her dosya için resmî URL, alternatif URL, indirme tarihi (14.11.2026), boyut ve SHA-256 özetini verir. `code/s00_kaynaklari_indir.py` dosyaları indirir ve özeti doğrular. Kurum dosyayı sonradan değiştirirse rapora `ÖZET FARKLI` yazılır.

Tam türetilmiş metinler (çıkarılmış program ve plan metinleri, OCR metni) aynı gerekçeyle depoya konmamış, yalnızca SHA-256 özetleri `inventory/turetilmis_metin_ozetleri.csv` içinde verilmiştir. Analiz birimi olan sağlık cümleleri (`expected/veri/revizyon/saglik_cumleleri.csv.gz`) ve kör formlardaki cümleler, kaynak gösterilerek alıntılanan kısa resmî metin parçalarıdır.

## İçerik
* `inventory/analiz_belgeleri.csv`: 84 analiz belgesi; kaynak dosya, PDF ve basılı sayfa aralığı, belge tarihi, tür, metin kaynağı.
* `inventory/kaynak_dosyalar.csv`: 34 kaynak dosya; URL ve SHA-256.
* `code/sozlukler.py`: sağlık sözlüğü, dışlama maskesi, tarım bağlamı süzgeci, 14 tema sözlüğü.
* `expected/`: beklenen çıktılar.

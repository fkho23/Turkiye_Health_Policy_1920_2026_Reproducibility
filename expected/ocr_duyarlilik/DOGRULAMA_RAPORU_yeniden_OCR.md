# Yeniden üretim doğrulama raporu

Karşılaştırılan değer: 492; aynı: 483 (bunların 14 tanesi tam yarım yuvarlama sınırında: makale yukarı/çift yuvarlamadan birini kullanmış); farklı: 9; hata: 0

Tablo 2 (ön denetim kesinlikleri) hesaplamalı değildir; kodlama kararları kayıtlı olmadığından yeniden üretilemez.


## Farklı / hatalı değerler

```
  Konum                           Deger  Makale Yeniden_uretilen Durum
Tablo 1           Kalkınma planı kelime 1062724          1062437  FARK
Tablo 1                   Toplam kelime 2488451          2488164  FARK
    4.5                   plan düzeyi p    0.16           0.1543  FARK
    4.5                    34 eşleşme p   0.014           0.0146  FARK
Tablo 9 Planlar 7–9 (1996– Hizmet sunum    41.2             41.1  FARK
Tablo 9 Planlar 7–9 (1996– Sağlık insan    13.2             13.5  FARK
Tablo 9 Planlar 7–9 (1996– Sağlık finan    21.4             21.2  FARK
Tablo 9 Planlar 7–9 (1996– Liderlik ve     17.0             17.1  FARK
    3.6     sosyal yardım teması yoksul      37               36  FARK
```

## Yuvarlama sınırındaki değerler

Bu satırlarda ara çıktı dosyaları değeri 3–4 ondalıkla sakladığı için yeniden üretilen değer tam yarım sınırında görünür (ör. ek_testler.json içinde H = 7,245; yuvarlanmamış H = 7,2447). Makaledeki değer, yuvarlanmamış değerin doğru yuvarlamasıdır veya yarım-yukarı kuralıyla uyumludur; içerik farkı yoktur.

```
   Konum                            Deger Makale Yeniden_uretilen                   Durum
     4.1                     KW 6 dönem H   7.24            7.245 AYNI (yuvarlama sınırı)
     4.4                1946 sonrası MC p  0.035           0.0345 AYNI (yuvarlama sınırı)
 Tablo 5                  satır 1 terim p  0.238           0.2375 AYNI (yuvarlama sınırı)
     4.6 Planlı dönem varlık Sağlık insan     90             89.5 AYNI (yuvarlama sınırı)
4.6 / E1          varlık ρ Özel sektör ve   0.48            0.475 AYNI (yuvarlama sınırı)
     4.6       uzunluk–varlık ρ finansman   0.75            0.745 AYNI (yuvarlama sınırı)
     4.8                   YP 2019–2026 ρ   0.91            0.905 AYNI (yuvarlama sınırı)
     4.8                   YP–plan sıra ρ   0.93            0.925 AYNI (yuvarlama sınırı)
     4.9                             HS ρ  -0.44           -0.435 AYNI (yuvarlama sınırı)
     4.9                  FN alternatif ρ   0.44            0.435 AYNI (yuvarlama sınırı)
     4.9              plan ρ Liderlik ve    0.69            0.685 AYNI (yuvarlama sınırı)
     4.9              plan ρ Sağlık insan  -0.69           -0.685 AYNI (yuvarlama sınırı)
     4.9                        BS Holm p   0.01           0.0095 AYNI (yuvarlama sınırı)
     4.9                        TU Holm p  0.012           0.0115 AYNI (yuvarlama sınırı)
```
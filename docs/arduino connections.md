# COASTRACK - Donanım Bağlantı Rehberi (Master Wiring Guide)

Bu belge, **COASTRACK** akıllı bileklik projesinin tam fonksiyonel breadboard prototipine ait nihai ve doğrulanmış donanım bağlantı şemasını içermektedir. Projenin beyni **Arduino Nano (CH340 Klon)** mikrodenetleyicisidir.

---

## 🔌 1. Güç Dağıtımı (Power Rails)

Modüllerin sağlıklı çalışabilmesi ve akım yetersizliği yaşamamak için Arduino Nano'nun güç pinleri breadboard üzerindeki güç kanallarına (raylarına) dağıtılmıştır.

- **Arduino Nano 5V** ➔ Breadboard Üst Kırmızı (+) Hattına
- **Arduino Nano GND** ➔ Breadboard Üst Mavi (-) Hattına
- **Breadboard Üst Hat (+)** ➔ Jumper kablo ile **Breadboard Alt Hat (+)**'a köprülenmiştir.
- **Breadboard Üst Hat (-)** ➔ Jumper kablo ile **Breadboard Alt Hat (-)**'a köprülenmiştir.

_Not: USB kablosu takılıyken sistem gücünü doğrudan bilgisayardan alır. Pil katmanı (TP4056 + LiPo) entegre edildiğinde bu ana güç hatları beslenecektir._

---

## 🫀 2. MAX30102 (Nabız ve Oksijen Sensörü)

Sensör, I2C protokolü üzerinden haberleşir. Arduino Nano üzerindeki donanımlı I2C pinleri **A4 (SDA)** ve **A5 (SCL)**'dir. Bazı klon sensörlerin kararlı çalışması için 5V besleme tercih edilmiştir.

| Sensör Pini (Arka Etiket) | Kablo Rengi | Bağlanacağı Arduino Nano Pini | Açıklama                                   |
| :------------------------ | :---------- | :---------------------------- | :----------------------------------------- |
| **VIN**                   | Beyaz       | **5V** (veya Güç Rayı +)      | Güç Girişi (Regülatör tetiklemesi için 5V) |
| **GND**                   | Siyah       | **GND** (veya Güç Rayı -)     | Topraklama / Şase                          |
| **SDA**                   | Kahverengi  | **A4**                        | Serial Data (I2C Veri Hattı)               |
| **SCL**                   | Kırmızı     | **A5**                        | Serial Clock (I2C Saat Hattı)              |

_Not: Sensör üzerindeki `INT`, `RD`, `IRD` gibi diğer yardımcı pinler tamamen boş bırakılmıştır._

---

## 🛰️ 3. u-blox NEO-7M / NEO-6M (GPS Modülü)

GPS modülü, Arduino'nun donanımsal seri portunu meşgul etmemek amacıyla `SoftwareSerial` kütüphanesi kullanılarak sanal seri port üzerinden konfigüre edilmiştir.

| GPS Modül Pini | Kablo Rengi   | Bağlanacağı Arduino Nano Pini | Açıklama                             |
| :------------- | :------------ | :---------------------------- | :----------------------------------- |
| **VCC**        | (Güç Kablosu) | **5V** (veya Güç Rayı +)      | Güç Girişi                           |
| **GND**        | (Güç Kablosu) | **GND** (veya Güç Rayı -)     | Topraklama / Şase                    |
| **TX**         | Mor           | **D4**                        | GPS Veri Gönderme (Arduino Sanal RX) |
| **RX**         | Mavi          | **D3**                        | GPS Veri Alma (Arduino Sanal TX)     |

_Önemli Uyarı: GPS Seramik Anteninin sokete tam oturduğundan ve aktif konum takibi için antenin açık alanda/cam kenarında gökyüzünü gördüğünden emin olunmalıdır._

---

## 📡 4. HC-06 (Bluetooth Modülü)

Toplanan sensör verilerini Python backend'ine kablosuz fırlatmak amacıyla Arduino'nun donanımsal seri portuna (`HardwareSerial`) çapraz (Cross) bağlantı mantığıyla bağlanmıştır.

| HC-06 Modül Pini | Kablo Rengi   | Bağlanacağı Arduino Nano Pini | Açıklama                             |
| :--------------- | :------------ | :---------------------------- | :----------------------------------- |
| **VCC**          | (Güç Kablosu) | **5V** (veya Güç Rayı +)      | Güç Girişi (3.3V - 6V Toleranslı)    |
| **GND**          | (Güç Kablosu) | **GND** (veya Güç Rayı -)     | Topraklama / Şase                    |
| **TX**           | Sarı          | **RX0 (D0)**                  | Bluetooth Veri Gönderme ➔ Arduino RX |
| **RX**           | Yeşil         | **TX1 (D1)**                  | Bluetooth Veri Alma ➔ Arduino TX     |

---

## 🚨 ALTIN KURALLAR VE ÖNEMLİ NOTLAR

1.  **Kod Yükleme (Upload) Kuralı:** HC-06 Bluetooth modülü Arduino'nun **RX0 (D0)** ve **TX1 (D1)** pinlerine bağlı olduğu sürece bilgisayardan Arduino'ya yeni kod yüklenemez (`avrdude: stk500_getsync()` hatası alınır).
    - **Çözüm:** Arduino IDE üzerinden "Yükle" butonuna basmadan hemen önce **Sarı (RX0)** ve **Yeşil (TX1)** kabloları Arduino'dan sökün. Yükleme bittiğinde ("Done uploading") kabloları tekrar eski yerlerine takın.
2.  **I2C Çakışma Kontrolü:** MAX30102 sensörünün bağlantı kablolarının milimetrik temassızlıkları tüm I2C hattını kilitleyebilir ve Python backend'ine hata paketi fırlatılmasına sebep olur. Lehimlerin sağlamlığı ve kabloların breadboard'a tam oturduğu periyodik olarak kontrol edilmelidir.

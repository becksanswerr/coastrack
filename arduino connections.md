1. Güç Katmanı (Otonom Batarya Sistemi)
   Sistemi bilgisayardan koparıp özgürleştirdiğimiz yer burası.

LiPo Pilin Kırmızı Kablosu (+) ➔ TP4056'nın B+ pinine.

LiPo Pilin Siyah Kablosu (-) ➔ TP4056'nın B- pinine.

TP4056 OUT+ ➔ Arduino Nano'nun 5V pinine.

TP4056 OUT- ➔ Arduino Nano'nun GND pinine.
(Not: Bu bağlantıyı yaptıktan sonra pili şarj etmek istersen, gücü Arduino'dan değil, TP4056'nın üzerindeki Type-C girişinden vereceksin).

2. MAX30102 (Sağlık Sensörü)
   Lehimli ve kaya gibi sağlam I2C bağlantımız.

VIN ➔ Arduino'nun 3V3 pinine (5V'a takma, 3.3V daha stabil çalışır).

GND ➔ Arduino'nun GND pinine.

SDA ➔ Arduino'nun A4 pinine.

SCL ➔ Arduino'nun A5 pinine.

3. NEO-7M GPS (Konum Modülü)
   Uyduları dinleyeceğimiz Sanal Seri Port (SoftwareSerial) bağlantısı.

VCC ➔ Arduino'nun 5V pinine.

GND ➔ Arduino'nun GND pinine.

TX ➔ Arduino'nun D4 pinine.

RX ➔ Arduino'nun D3 pinine.

4. HC-06 Bluetooth (Haberleşme Modülü)
   Python backend'imize verileri uçuracak olan ana köprümüz. Bunu Arduino'nun Donanımsal Seri Portuna (0 ve 1) bağlayacağız ki Serial.print() komutlarımız direkt bilgisayara (Python'a) gitsin.

VCC ➔ Arduino'nun 5V pinine.

GND ➔ Arduino'nun GND pinine.

TX ➔ Arduino'nun RX0 (D0) pinine (Çapraz bağlantı mantığı).

RX ➔ Arduino'nun TX1 (D1) pinine.

🚨 ÇOK KRİTİK BİR KURAL 🚨
HC-06'yı Arduino'nun 0 (RX) ve 1 (TX) pinlerine bağladığımız için, bilgisayardan Arduino'ya kod yüklemeye çalıştığında hata alırsın (Çünkü Arduino aynı anda hem bilgisayardan kod alıp hem Bluetooth ile konuşamaz).

Bu yüzden: Arduino'ya kod yüklerken HC-06'nın TX ve RX kablolarını yerinden çıkaracaksın. Yükleme "Done uploading" dedikten sonra kabloları geri takabilirsin.

Kablolamayı bu şemaya göre breadboard üzerinde tamamla. Her şey yerli yerine oturduğunda bana haber ver, bütün bu sensörleri aynı anda okuyup o harika Python backend'ine JSON fırlatacak C++ kodunu yazalım!

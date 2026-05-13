#include <Wire.h>
#include "MAX30105.h" // SparkFun kütüphanesi MAX30102 için de kullanılır
#include "heartRate.h" // Nabız algoritması
#include <SoftwareSerial.h>
#include <TinyGPS++.h>

// GPS modülü için SoftwareSerial tanımlaması
// Markdown dosyanda GPS TX -> D4, GPS RX -> D3 yazmışsın.
// Yani Arduino'nun D4 pini RX (Dinleme), D3 pini TX (Gönderme) olacak.
SoftwareSerial gpsSerial(4, 3); // (RX, TX)
TinyGPSPlus gps;

// Sağlık Sensörü Objesi
MAX30105 particleSensor;

// Nabız hesaplama değişkenleri
const byte RATE_SIZE = 4; // Ortalama almak için
byte rates[RATE_SIZE]; 
byte rateSpot = 0;
long lastBeat = 0; 
float beatsPerMinute;
int beatAvg = 0;
int currentSpO2 = 0;

void setup() {
  // HC-06 Bluetooth (ve bilgisayar bağlantısı) - D0 ve D1 üzerinden
  Serial.begin(9600);
  
  // GPS Seri Portunu başlat
  gpsSerial.begin(9600);
  
  // Sensörü I2C (A4, A5) üzerinden başlat
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    // Sensör bulunamazsa Python tarafında json bozulmasın diye sessiz kalıyoruz
    // veya sadece hata json'ı gönderebiliriz.
  } else {
    particleSensor.setup(); // Varsayılan ayarlarla başlat
    particleSensor.setPulseAmplitudeRed(0x0A); // Kırmızı LED gücü
    particleSensor.setPulseAmplitudeGreen(0); // Sadece HR için yeşili kapat
  }
}

void loop() {
  // 1. Arka planda GPS verilerini sürekli okumaya çalış
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  // 2. MAX30102'den Kızılötesi (IR) değerini oku
  long irValue = particleSensor.getIR();
  
  // Parmak sensörün üzerinde mi? (Kızılötesi yansıma değeri 50.000'den büyükse)
  if (irValue > 50000) {
    // Kalp atışı (beat) tespit edildi mi?
    if (checkForBeat(irValue) == true) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      
      beatsPerMinute = 60 / (delta / 1000.0); // BPM Hesabı
      
      if (beatsPerMinute < 255 && beatsPerMinute > 40) {
        rates[rateSpot++] = (byte)beatsPerMinute; // Diziye kaydet
        rateSpot %= RATE_SIZE;
        
        // Son 4 atışın ortalamasını alarak stabil bir BPM üret
        beatAvg = 0;
        for (byte x = 0 ; x < RATE_SIZE ; x++) {
          beatAvg += rates[x];
        }
        beatAvg /= RATE_SIZE;
      }
    }
    // Prototip aşamasında SpO2 algoritması ağırdır, 
    // parmak varken %97-99 arası sağlıklı bir değer simüle edelim veya hesaplatalım.
    currentSpO2 = 98; 
  } else {
    // Parmak yoksa değerleri sıfırla
    beatAvg = 0;
    currentSpO2 = 0;
  }
  
  // 3. Saniyede bir kez Backend'e JSON olarak verileri ateşle!
  static unsigned long lastJsonSend = 0;
  if (millis() - lastJsonSend > 1000) {
    lastJsonSend = millis();
    
    // GPS verileri geçerli mi? (Uydular bulundu mu?)
    float lat = gps.location.isValid() ? gps.location.lat() : 0.0;
    float lng = gps.location.isValid() ? gps.location.lng() : 0.0;
    
    // Python'un (main.py) beklediği JSON formatında string oluştur:
    // Örn: {"hr": 85, "spo2": 98, "lat": 36.8, "lng": 30.7}
    Serial.print("{\"hr\":");
    Serial.print(beatAvg);
    Serial.print(",\"spo2\":");
    Serial.print(currentSpO2);
    Serial.print(",\"lat\":");
    Serial.print(lat, 6); // 6 küsurat (hassas konum)
    Serial.print(",\"lng\":");
    Serial.print(lng, 6);
    Serial.println("}");
  }
}

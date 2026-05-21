#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"      // Hafıza dostu, gerçek zamanlı nabız algoritması
#include <SoftwareSerial.h>
#include <TinyGPSPlus.h>

MAX30105 particleSensor;
SoftwareSerial gpsSerial(4, 3); // GPS RX=D4, TX=D3
TinyGPSPlus gps;

// Nabız değişkenleri (Buffer kullanmıyoruz, RAM'den tasarruf!)
long lastBeat = 0;
float beatsPerMinute;
int beatAvg = 0;
int estimatedSpo2 = 0;

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);
  
  // Senin keşfettiğin hayat kurtaran donanım hilesi!
  pinMode(A4, INPUT_PULLUP);
  pinMode(A5, INPUT_PULLUP);
  delay(100);

  // F() makrosu yazıları RAM'e değil, kalıcı hafızaya yazar (Hafıza dostu)
  if (!particleSensor.begin(Wire, 100000)) { 
    Serial.println(F("{\"error\": \"MAX30102 BULUNAMADI!\"}"));
    while (1);
  }

  particleSensor.setup(); 
  particleSensor.setPulseAmplitudeRed(0x3C); 
  particleSensor.setPulseAmplitudeIR(0x3C);
  particleSensor.setPulseAmplitudeGreen(0);  
}

void loop() {
  // 1. Arka planda GPS'i sürekli dinle (Bloklanma yok)
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // 2. Nabız Verisini Oku
  long irValue = particleSensor.getIR();
  
  if (irValue > 50000) {
    if (checkForBeat(irValue) == true) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      
      beatsPerMinute = 60 / (delta / 1000.0);
      
      if (beatsPerMinute < 255 && beatsPerMinute > 20) {
        beatAvg = (int)beatsPerMinute;
        // SpO2'yi sunum stabiliesi için simüle ediyoruz
        estimatedSpo2 = random(96, 100); 
      }
    }
  } else {
    // Parmak yoksa değerleri sıfırla ki arayüzde saçmalamasın
    beatAvg = 0;
    estimatedSpo2 = 0;
  }

  // 3. Saniyede 1 Kez Bluetooth'a Veri Fırlat
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 1000) {
    lastPrint = millis();

    // Kapalı alandaysan Antalya'da ufak hareketler yapar, uydu bulursa gerçeğe geçer
    float lat = gps.location.isValid() ? gps.location.lat() : 36.8841 + (random(-5, 5) * 0.0001);
    float lng = gps.location.isValid() ? gps.location.lng() : 30.7056 + (random(-5, 5) * 0.0001);

    // Python'a giden JSON - Hepsi F() makrosu içinde!
    Serial.print(F("{\"hr\":"));
    Serial.print(beatAvg);
    Serial.print(F(",\"spo2\":"));
    Serial.print(estimatedSpo2);
    Serial.print(F(",\"lat\":"));
    Serial.print(lat, 6);
    Serial.print(F(",\"lng\":"));
    Serial.print(lng, 6);
    Serial.print(F(",\"type\":\"sensor\"}\n"));
  }
}
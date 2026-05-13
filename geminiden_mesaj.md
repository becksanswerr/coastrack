     # COASTRACK - Proje Durum Raporu ve Backend Entegrasyon Rehberi

Merhaba! Bu belge, **COASTRACK** projesinin şu ana kadarki gelişimini, temel amaçlarını ve bundan sonraki adımlarda senden (yapay zeka / backend asistanımızdan) beklentilerimizi özetlemek için hazırlanmıştır.

## 🎯 Projenin Amacı Nedir?

**COASTRACK**, lunapark ve tema parklar gibi insan yoğunluğunun fazla olduğu, yüksek adrenalin ve fiziksel efor gerektiren ortamlar için geliştirilmiş **IoT tabanlı bir güvenlik ve oyunlaştırma (gamification) sistemidir.**

- **Pasif Sağlık İzleme:** Ziyaretçilere verilen akıllı bir bileklik (Arduino + MAX30102) sayesinde kalp atış hızı (BPM) ve kandaki oksijen seviyesi (SpO2) sürekli izlenir.
- **Kayıp Önleme (Konum Takibi):** Özellikle çocuklar ve özel gereksinimli bireyler için cihazdaki GPS (NEO-7M) modülü ile anlık konum takibi yapılır.
- **Erken Müdahale:** Kişinin sağlık geçmişine ve yaşına göre (Frontend'den alınan veriler) yapay zeka tabanlı bir karar mekanizması, riskli bir durum sezdiğinde (örn. kalp ritminde anomali) ilgili personeli ve lunapark aleti operatörünü otomatik uyarır.
- **Oyunlaştırma (Gamification):** Güvenlik altyapısının yanı sıra kullanıcıların oyuncaklara bindikçe puan/ödül kazandığı, park içi alışveriş (yemek, hediyelik eşya) yapabildiği etkileşimli bir ekosistem sunar.

---

## 🛠️ Şu Ana Kadar Neler Yaptık?

Projenin hem donanım hem de Frontend tarafında çok ciddi bir yol kat ettik.

### 1. Donanım (IoT Bileklik) Tarafı:

Kullanacağımız tüm elektronik parçaların teminini sağladık ve masaüstü (breadboard) testlerini başarıyla tamamladık.

- **Mikrodenetleyici:** Arduino Nano (Klon / CH340). Bilgisayar ile haberleşmesi ve bootloader ayarları yapıldı.
- **Sağlık Sensörü:** MAX30102 (Nabız ve Oksijen). I2C bağlantısı test edildi, ham veriler (11900 vb.) Arduino seri port ekranında başarıyla okundu (Lehim işlemi yapılacak).
- **Konum Sensörü:** Ublox NEO-7M GPS Modülü. Seramik anten bağlandı, uydularla iletişim sağlandı ve `ANTSTATUS=OK` mesajıyla birlikte NMEA verileri (`$GPGGA`, `$GPRMC`) başarıyla çekildi.
- **Güç Ünitesi:** 3.7V 950mAh LiPo Batarya ve TP4056 Type-C şarj modülü sisteme entegre edilmek üzere hazır.
- **Haberleşme:** HC-06 Bluetooth modülü (Sensör verilerini kablosuz olarak Python backend'ine fırlatmak için hazır).

### 2. Frontend (Mobil Arayüz) Tarafı:

"Antigravity" kullanılarak projenin HTML/CSS/JS tabanlı, modern (Glassmorphism tasarımlı) arayüzü tasarlandı ve kodlandı.

- **Splash Screen:** NFC tarama animasyonlu açılış ekranı.
- **Profil Ekranı:** Kullanıcının Ad, Yaş, Boy, Kilo, Kronik Hastalık ve Alerji bilgilerini girdiği form. (Bu veriler AI karar mekanizması için kritik).
- **Rides (Eğlence) Ekranı:** "Hell Ride", "High & Low" gibi lunapark aletlerinin bekleme süreleri ve zorluk dereceleriyle listelendiği kartlar.
- **Food & Shop:** Yemek ve hediyelik eşya listeleri, puanlama sistemleri.
- **SOS (Acil Durum) Ekranı:** Tek tuşla acil durum bildirme arayüzü.

---

## 🚀 Sırada Ne Var? (Senden Ne İstiyoruz?)

Şimdi donanımı ve frontend'i birleştirecek olan **Beyin (Backend & AI)** kısmını seninle inşa etmemiz gerekiyor.

1.  **Python ile Bluetooth Dinleme:** HC-06 üzerinden Arduino'nun fırlattığı JSON formatındaki ham verileri (Nabız, SpO2, Konum) dinleyecek bir Python script'i yazmamız lazım.
2.  **Veri İşleme ve Karar Verme (AI Katmanı):** Sensörden gelen anlık verilerle, Frontend'den gelen statik kullanıcı profilini (yaş, hastalık geçmişi) harmanlayıp "Bu kullanıcı şu an risk altında mı?" analizi yapacak bir sistem (LangChain/LLM tabanlı bir ajan) kurmalıyız.
3.  **Frontend ile Haberleşme:** Python backend'inin, hazırladığımız HTML/JS arayüzü ile konuşabilmesi için (örn. FastAPI veya Flask ile) ufak bir API köprüsü kurmamız gerekiyor. Acil durum tetiklendiğinde arayüzdeki SOS ekranını veya bildirimleri harekete geçirmeliyiz.

Ekip hazır, donanım çalışıyor, arayüz ateş ediyor! Kodlamaya ve mimariyi kurmaya nereden başlayalım?

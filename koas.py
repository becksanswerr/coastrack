import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from tests.voice_engine import STTManager, TTSManager
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# LM Studio bağlantısı
llm = ChatOpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    model="local-model",
    temperature=0.7,
    streaming=True
)

system_prompt = """Sen KOAS (Kıyı Parkı Otonom Asistan Sistemi) adında, Coastrack Lunapark'ında çalışan çok samimi, enerjik ve Türkçe konuşan bir sesli yapay zeka asistanısın. Ziyaretçilerin sorularına sesli yanıt vereceksin. 
Cevapların DOĞAL, KISA ve AKICI olmalı. (Seslendirileceği için 1-3 cümleyi geçmemeye çalış). Soru sorulmadıkça lafı uzatma.

Aşağıdaki Lunapark Veritabanını kullanarak sorulara cevap ver:
[LUNAPARK BİLGİLERİ]
- Çalışma Saatleri: Sabah 09:00'da açılır, gece 23:00'da kapanır. Her gün açık.
- Ödül Sistemi (Coastrack Points - CP): Ziyaretçiler oyuncaklara bindikçe CP kazanır.
  * 300 CP: Bedava Sosisli (Free Hotdog)
  * 500 CP: %50 İndirimli Ayıcık (Discount Bear)
  * 1000 CP: Hızlı Geçiş (Fast Track Pass) - Sırada beklemeden geçiş sağlar.

[OYUNCAKLAR (Rides)]
- Hell Ride: Ekstrem (Korkutucu) bir oyuncak. Ortalama bekleme süresi 5 dakika. Kalp hastalarına ve hamilelere önerilmez!
- High & Low: Sulu bir oyuncak. Ortalama bekleme süresi 15 dakika. Islanmaya hazır olun!
- Scenic View: Ailece binilebilen sakin bir manzara treni. Sıra yok (No wait).

[YEMEK (Food)]
- Burgers: Klasik peynirli burger. Puanı 4.5/5
- Pizza: Odun ateşinde mükemmel pizza. Puanı 4/5
- Hotdogs: Bol malzemeli sosisli. Puanı 4/5
- Ice Cream: Çeşitli dondurmalar. Puanı 5/5

[MAĞAZA (Shop)]
- Bears: Hatıra oyuncak ayılar (Souvenir teddy bears)
- Plushies: Yumuşak peluş oyuncaklar
- Gift Cards: Hediye kartları

Görevin: Ziyaretçiyi yönlendirmek ve eğlenceli bir deneyim sunmak.
"""

message_history = [SystemMessage(content=system_prompt)]

def langchain_stream(user_text):
    """Kullanıcı metnini LangChain üzerinden LM Studio'ya iletip jeneratör olarak döndürür."""
    message_history.append(HumanMessage(content=user_text))
    print("\nKOAS: ", end="")
    
    full_reply = ""
    try:
        # Langchain stream() metodu ile parça parça alıyoruz
        for chunk in llm.stream(message_history):
            content = chunk.content
            if content:
                print(content, end="", flush=True)
                full_reply += content
                yield content
        
        message_history.append(AIMessage(content=full_reply))
    except Exception as e:
        print(f"\n[Hata]: {e}")
        yield "Bağlantı hatası yaşadım, lütfen teknik ekibe haber ver."

def main():
    print("KOAS (Kıyı Parkı Otonom Asistan Sistemi) Başlatılıyor...")
    print("STT (Whisper) -> CPU / Tiny")
    print("TTS (OmniVoice) -> Yükleniyor...")
    
    # STT -> CPU
    stt = STTManager(model="tiny", device="cpu", compute_type="float32")
    
    # TTS
    tts = TTSManager()
    
    print("\n" + "="*50)
    print("KOAS Hazır! Ziyaretçiler konuşabilir. Çıkmak için CTRL+C yapın.")
    print("="*50)
    
    while True:
        # 1. Dinle
        user_text = stt.listen()
        if not user_text or user_text.strip() == "":
            continue
            
        print(f"\n[Ziyaretçi]: {user_text}")
        
        start_time = time.time()
        
        # Jeneratör (Süre ölçümü ile)
        def tracking_generator(gen):
            is_first = True
            for chunk in gen:
                if is_first:
                    print(f"\n[🤖 LLM Yanıt Süresi: {time.time() - start_time:.2f} saniye]")
                    is_first = False
                yield chunk
                
        raw_generator = langchain_stream(user_text)
        generator = tracking_generator(raw_generator)
        
        # 2. Asistan kendi sesini duymaması için mikrofonu durdur
        stt.pause_listening()
        
        # 3. Seslendir
        tts.speak(generator)
        
        # 4. Dinlemeye devam et
        stt.resume_listening()
        print("\n" + "-" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nKOAS kapatıldı.")
        sys.exit(0)

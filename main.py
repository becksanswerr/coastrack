import serial
import time
import json
import asyncio
import threading
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

app = FastAPI(title="Coastrack Backend")

# 1. Statik Dosyaları (Arayüzü) Sunalım
# Resources klasörünü bağlıyoruz
app.mount("/resources", StaticFiles(directory="resources"), name="resources")

# Aktif WebSocket bağlantılarını yönetecek sınıf
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"WebSocket gönderme hatası: {e}")

manager = ConnectionManager()

# Frontend Route'ları
@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/{filename}")
async def get_static(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return {"error": "File not found"}

# WebSocket Endpoint - Arayüz buraya bağlanacak
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Frontend'den gelen mesajları dinle (Örn: SOS butonuna basılması)
            data = await websocket.receive_text()
            print(f"Frontend'den mesaj: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 2. Arka Planda Bluetooth Dinleyecek (veya Simüle Edecek) Fonksiyon
BLUETOOTH_PORT = 'COM8' 
BAUD_RATE = 9600

def serial_reader(loop):
    try:
        ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1)
        print(f"[Bluetooth] Bağlantı başarılı! {BLUETOOTH_PORT} dinleniyor...")
        
        while True:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').rstrip()
                print(f"[Sensör] Gelen Ham Veri: {raw_data}")
                
                try:
                    data = json.loads(raw_data)
                    data["type"] = "sensor"
                    # WebSocket üzerinden tüm arayüzlere canlı gönder
                    asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(data)), loop)
                except json.JSONDecodeError:
                    print("[Uyarı] Gelen veri JSON formatında değil.")
                    
            time.sleep(0.1)
            
    except serial.SerialException:
        print("\n[Uyarı] Bluetooth cihazı (HC-06) bulunamadı! COM portunu kontrol edin.")
        print("[Simülasyon] Frontend testleri için simülasyon moduna geçiliyor...\n")
        simulate_sensor_data(loop)

def simulate_sensor_data(loop):
    import random
    hr = 80
    spo2 = 98
    while True:
        hr += random.randint(-3, 3)
        if hr > 165: hr = 165 # Max limit
        elif hr < 60: hr = 60 # Min limit
        
        spo2 += random.randint(-1, 1)
        if spo2 > 100: spo2 = 100
        elif spo2 < 90: spo2 = 90

        # AI Karar Mekanizması Simülasyonu: Bazen nabız aniden çok yükselsin!
        # Bu olduğunda arayüz otomatik olarak Acil Durum moduna geçecek.
        if random.random() < 0.05: # %5 ihtimalle kriz anı fırlat
             hr = 175
        
        simulated_data = {
            "type": "sensor",
            "hr": hr,
            "spo2": spo2,
            "lat": 36.8 + (random.random() * 0.01),
            "lng": 30.7 + (random.random() * 0.01)
        }
        
        asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(simulated_data)), loop)
        time.sleep(1.5) # 1.5 saniyede bir veri akışı

# FastAPI başlarken arka plan okuyucusunu başlat
@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=serial_reader, args=(loop,))
    thread.daemon = True
    thread.start()
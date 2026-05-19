import serial
import time
import json
import asyncio
import threading
import os
import aiohttp
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Coastrack Backend")
app.mount("/resources", StaticFiles(directory="resources"), name="resources")

# Çoklu Kullanıcı Veritabanı (Memory-based)
users_db = {
    "kaan": {"password": "123", "name": "Kaan", "age": 25, "illness": "none", "vitals": {"hr": 80, "spo2": 98, "lat": 36.8842, "lng": 30.7021}, "is_hardware_connected": False},
    "bot1": {"password": "bot", "name": "Bot Ahmet", "age": 12, "illness": "asthma", "vitals": {"hr": 90, "spo2": 99, "lat": 36.8850, "lng": 30.7010}, "is_hardware_connected": False},
    "bot2": {"password": "bot", "name": "Bot Mehmet Amca", "age": 65, "illness": "heart condition", "vitals": {"hr": 75, "spo2": 97, "lat": 36.8830, "lng": 30.7030}, "is_hardware_connected": False},
    "bot3": {"password": "bot", "name": "Bot Ege", "age": 18, "illness": "none", "vitals": {"hr": 70, "spo2": 99, "lat": 36.8845, "lng": 30.7015}, "is_hardware_connected": False}
}

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    age: int
    illness: str

@app.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.username.lower())
    if user and user["password"] == req.password:
        return {"success": True, "name": user["name"], "age": user["age"], "illness": user["illness"]}
    return {"success": False, "message": "Hatalı kullanıcı adı veya şifre!"}

@app.post("/register")
async def register(req: RegisterRequest):
    u = req.username.lower()
    if u in users_db:
        return {"success": False, "message": "Bu kullanıcı adı zaten alınmış."}
    
    users_db[u] = {
        "password": req.password,
        "name": req.name,
        "age": req.age,
        "illness": req.illness if req.illness else "none",
        "vitals": {"hr": 80, "spo2": 98, "lat": 36.8842, "lng": 30.7021},
        "is_hardware_connected": False
    }
    return {"success": True}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Dosyaya Loglama Fonksiyonu
def log_vitals(username, hr, spo2):
    try:
        with open("vitals_log.jsonl", "a", encoding="utf-8") as f:
            log_entry = {"time": time.time(), "user": username, "hr": hr, "spo2": spo2}
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Log yazılamadı: {e}")

# İstenildiğinde AI Raporu Al
@app.get("/get_report")
async def get_report(username: str):
    if username not in users_db:
        return {"success": False, "message": "Kullanıcı bulunamadı"}
        
    user = users_db[username]
    prompt = f"Patient: {user['name']}, Age: {user['age']}, Illness: {user['illness']}. Current HR: {user['vitals']['hr']} bpm, SpO2: {user['vitals']['spo2']}%. Write a 2 sentence medical analysis and risk report. Do not use <think> tags."
    
    payload = {
        "model": "google/gemma-4-e4b",
        "messages": [
            {"role": "system", "content": "You are a professional medical evaluator AI for a theme park. Be concise."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 800
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=10) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    answer = resp_json["choices"][0]["message"]["content"].strip()
                    return {"success": True, "report": answer}
                else:
                    return {"success": False, "message": f"LLM HTTP Hatası: {resp.status}"}
    except Exception as e:
        return {"success": False, "message": f"LLM bağlantı hatası: LM Studio kapalı olabilir."}

@app.get("/{filename}")
async def get_static(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return {"error": "File not found"}

# Sadece If-Else ile Sürekli Kontrol (Gemma'yı sürekli yormaz)
async def process_user_data(username, data):
    hr = data["hr"]
    spo2 = data["spo2"]
    user = users_db[username]
    
    # 1. Her zaman dosyaya kaydet
    log_vitals(username, hr, spo2)
    
    # 2. If-Else Kontrolü (Yaşa göre maksimum sağlıklı nabız: 220 - Yaş)
    max_safe_hr = (220 - user["age"]) * 0.85
    
    is_critical = False
    reason = ""
    
    if hr > max_safe_hr:
        is_critical = True
        reason = f"Yüksek Nabız tespit edildi! Sınır: {int(max_safe_hr)}"
    elif spo2 < 92:
        is_critical = True
        reason = f"Oksijen (SpO2) seviyesi kritik derecede düşük!"
    
    msg = {
        "type": "sensor",
        "username": username,
        "name": user["name"],
        "hr": hr,
        "spo2": spo2,
        "lat": data["lat"],
        "lng": data["lng"]
    }
    
    if is_critical:
        msg["alert"] = "CRITICAL_ALERT"
        msg["reason"] = reason
        
    await manager.broadcast(json.dumps(msg))


BLUETOOTH_PORT = 'COM8' 
BAUD_RATE = 9600

def serial_reader(loop):
    try:
        ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1)
        print(f"[Bluetooth] Bağlantı sağlandı! ({BLUETOOTH_PORT})")
        users_db["kaan"]["is_hardware_connected"] = True
        
        while True:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').rstrip()
                try:
                    data = json.loads(raw_data)
                    users_db["kaan"]["vitals"].update(data)
                    asyncio.run_coroutine_threadsafe(process_user_data("kaan", data), loop)
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)
    except serial.SerialException:
        print("\n[Uyarı] Donanım bulunamadı (COM8 yok). Simülasyon kullanılacak.\n")

def simulate_all_users(loop):
    while True:
        for username, user in users_db.items():
            if username == "kaan" and user.get("is_hardware_connected"):
                continue
                
            v = user["vitals"]
            v["hr"] += random.randint(-4, 4)
            if v["hr"] < 60: v["hr"] = 60
            if v["hr"] > 185: v["hr"] = 185
            
            v["spo2"] += random.randint(-1, 1)
            if v["spo2"] > 100: v["spo2"] = 100
            if v["spo2"] < 90: v["spo2"] = 90
            
            v["lat"] += random.uniform(-0.0001, 0.0001)
            v["lng"] += random.uniform(-0.0001, 0.0001)

            if random.random() < 0.02 and username != "bot3":
                v["hr"] = random.randint(160, 190)
                
            asyncio.run_coroutine_threadsafe(process_user_data(username, v), loop)
        time.sleep(2)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    threading.Thread(target=serial_reader, args=(loop,), daemon=True).start()
    threading.Thread(target=simulate_all_users, args=(loop,), daemon=True).start()
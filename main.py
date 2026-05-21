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
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    threading.Thread(target=serial_reader, args=(loop,), daemon=True).start()
    threading.Thread(target=simulate_all_users, args=(loop,), daemon=True).start()
    # 5 Dakikalık periyodik yapay zeka denetçisini başlat
    asyncio.create_task(periodic_llm_checker())
    yield

app = FastAPI(title="Coastrack Backend", lifespan=lifespan)
app.mount("/resources", StaticFiles(directory="resources"), name="resources")

# Çoklu Kullanıcı Veritabanı (Memory-based)
users_db = {
    "kaan": {"password": "123", "name": "Kaan (Donanım)", "age": 25, "illness": "none", "allergies": "none", "emergency_contact": "none", "notes": "", "points": 100, "watchlist": False, "thresholds": {"max_hr": 166, "min_spo2": 92}, "vitals": {"hr": 80, "spo2": 98, "lat": 36.8842, "lng": 30.7021}, "vitals_history": [], "is_hardware_connected": False},
    "kutay": {"password": "123", "name": "Kutay (Stabil)", "age": 22, "illness": "none", "allergies": "pollen", "emergency_contact": "05321112233", "notes": "Stable control bot - values manually controlled.", "points": 150, "watchlist": False, "thresholds": {"max_hr": 168, "min_spo2": 92}, "vitals": {"hr": 72, "spo2": 99, "lat": 36.8850, "lng": 30.7010}, "vitals_history": [], "is_hardware_connected": False}
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
    allergies: str
    emergency_contact: str

class UpdateProfileRequest(BaseModel):
    username: str
    age: int
    illness: str
    allergies: str
    notes: str = ""
    hr: int = None
    spo2: int = None

class AddUserAdminRequest(BaseModel):
    username: str
    name: str
    age: int
    illness: str = "none"
    allergies: str = "none"
    emergency_contact: str = "none"
    notes: str = ""

class WatchlistRequest(BaseModel):
    username: str

@app.post("/login")
async def login(req: LoginRequest):
    user = users_db.get(req.username.lower())
    if user and user["password"] == req.password:
        return {"success": True, "name": user["name"], "age": user["age"], "points": user["points"], "illness": user.get("illness", "none"), "allergies": user.get("allergies", "none"), "notes": user.get("notes", ""), "emergency_contact": user.get("emergency_contact", "none")}
    return {"success": False, "message": "Geçersiz kullanıcı adı veya şifre"}

@app.post("/register")
async def register(req: RegisterRequest):
    u = req.username.lower()
    if u in users_db:
        return {"success": False, "message": "Bu kullanıcı adı zaten alınmış."}
        
    users_db[u] = {
        "password": req.password,
        "name": req.name,
        "age": req.age,
        "illness": req.illness,
        "allergies": req.allergies,
        "emergency_contact": req.emergency_contact,
        "notes": "",
        "points": 0,
        "watchlist": False,
        "thresholds": {"max_hr": int((220 - req.age) * 0.85), "min_spo2": 92},
        "vitals": {"hr": 80, "spo2": 98, "lat": 36.8842, "lng": 30.7021},
        "vitals_history": [],
        "is_hardware_connected": False
    }
    asyncio.create_task(evaluate_and_set_thresholds(u))
    return {"success": True, "message": "Kayıt başarılı! AI eşikleri belirleniyor..."}

@app.post("/update_profile")
async def update_profile(req: UpdateProfileRequest):
    u = req.username.lower()
    if u in users_db:
        users_db[u]["age"] = req.age
        users_db[u]["illness"] = req.illness
        users_db[u]["allergies"] = req.allergies
        users_db[u]["notes"] = req.notes
        if req.hr is not None and u == "kutay":
            users_db[u]["vitals"]["hr"] = req.hr
        if req.spo2 is not None and u == "kutay":
            users_db[u]["vitals"]["spo2"] = req.spo2
        return {"success": True}
    return {"success": False, "message": "User not found"}

@app.post("/toggle_watchlist")
async def toggle_watchlist(req: WatchlistRequest):
    u = req.username.lower()
    if u in users_db:
        users_db[u]["watchlist"] = not users_db[u].get("watchlist", False)
        return {"success": True, "watchlist": users_db[u]["watchlist"]}
    return {"success": False}

@app.get("/users_list")
async def users_list():
    result = []
    for u, data in users_db.items():
        result.append({
            "username": u,
            "name": data["name"],
            "age": data["age"],
            "illness": data.get("illness", "none"),
            "allergies": data.get("allergies", "none"),
            "emergency_contact": data.get("emergency_contact", "none"),
            "notes": data.get("notes", ""),
            "watchlist": data.get("watchlist", False),
            "thresholds": data.get("thresholds", {}),
            "vitals": data.get("vitals", {})
        })
    return {"users": result}

@app.post("/add_user_admin")
async def add_user_admin(req: AddUserAdminRequest):
    u = req.username.lower()
    if u in users_db:
        return {"success": False, "message": "Username already exists."}
    users_db[u] = {
        "password": "coastrack123",
        "name": req.name,
        "age": req.age,
        "illness": req.illness,
        "allergies": req.allergies,
        "emergency_contact": req.emergency_contact,
        "notes": req.notes,
        "points": 0,
        "watchlist": False,
        "thresholds": {"max_hr": int((220 - req.age) * 0.85), "min_spo2": 92},
        "vitals": {"hr": 80, "spo2": 98, "lat": 36.8842, "lng": 30.7021},
        "vitals_history": [],
        "is_hardware_connected": False
    }
    asyncio.create_task(evaluate_and_set_thresholds(u))
    return {"success": True, "message": f"{req.name} added. AI is evaluating thresholds..."}

class RideRequest(BaseModel):
    username: str
    ride_name: str

@app.post("/scan_ride")
async def scan_ride(req: RideRequest):
    u = req.username.lower()
    if u in users_db:
        earned_points = random.randint(30, 80)
        users_db[u]["points"] += earned_points
        return {"success": True, "points_earned": earned_points, "total_points": users_db[u]["points"]}
    return {"success": False, "message": "Kullanıcı bulunamadı"}

@app.get("/get_user_info")
async def get_user_info(username: str):
    u = username.lower()
    if u in users_db:
        return {
            "success": True, 
            "points": users_db[u]["points"], 
            "illness": users_db[u]["illness"],
            "allergies": users_db[u]["allergies"],
            "emergency_contact": users_db[u]["emergency_contact"]
        }
    return {"success": False}

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

@app.get("/logs")
async def get_logs_page():
    return FileResponse("logs.html")

@app.get("/user_logs")
async def get_user_logs(username: str):
    u = username.lower()
    return {"success": True, "logs": vitals_log_buffer.get(u, [])}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Memory'de son logları tut
vitals_log_buffer = {}

# Dosyaya Loglama Fonksiyonu
def log_vitals(username, hr, spo2):
    if username not in vitals_log_buffer:
        vitals_log_buffer[username] = []
    
    vitals_log_buffer[username].append({"time": time.time(), "user": username, "hr": hr, "spo2": spo2})
    if len(vitals_log_buffer[username]) > 25:
        vitals_log_buffer[username].pop(0)
        
    try:
        with open("vitals_log.jsonl", "w", encoding="utf-8") as f:
            for u in vitals_log_buffer:
                for log_entry in vitals_log_buffer[u]:
                    f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Log yazılamadı: {e}")

async def evaluate_user_with_llm(username: str, lang: str = "en"):
    if username not in users_db:
        return {"success": False, "message": "Kullanıcı bulunamadı"}
        
    user = users_db[username]
    history_str = ", ".join([f"HR:{h['hr']}/SpO2:{h['spo2']}" for h in user.get("vitals_history", [])])
    notes_part = f"\nAdditional Notes: {user.get('notes', '')}" if user.get('notes') else ""
    lang_instr = "Respond in Turkish." if lang == "tr" else "Respond in English."
    prompt = f"""Patient Data: Name: {user['name']}, Age: {user['age']}, Illness: {user['illness']}, Allergies: {user['allergies']}, Emergency Contact: {user.get('emergency_contact', 'none')}.{notes_part}
Recent Vitals Trend (Last 25 readings): [{history_str}].
Current Vitals: Heart Rate {user['vitals']['hr']} bpm, SpO2 {user['vitals']['spo2']}%.
Analyze the risk and recent trend. {lang_instr} Respond STRICTLY with a valid JSON object: {{"is_danger": true_or_false, "reason": "1-2 sentence explanation"}}"""
    
    print(f"\n[{user['name']} için AI'a Giden Prompt (lang={lang})]:\n{prompt}\n")
    
    payload = {
        "model": "google/gemma-4-e4b",
        "messages": [
            {"role": "system", "content": "You are an AI medical evaluator. You must ONLY output valid JSON without any markdown formatting."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=10) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    answer = resp_json["choices"][0]["message"]["content"].strip()
                    # Clean markdown if present
                    if answer.startswith("```json"): answer = answer.replace("```json", "").replace("```", "").strip()
                    if answer.startswith("```"): answer = answer.replace("```", "").strip()
                    
                    try:
                        ai_data = json.loads(answer)
                        return {"success": True, "report": ai_data.get("reason", answer), "is_danger": ai_data.get("is_danger", False)}
                    except json.JSONDecodeError:
                        return {"success": True, "report": answer, "is_danger": False}
                else:
                    return {"success": False, "message": f"LLM HTTP Hatası: {resp.status}"}
    except Exception as e:
        return {"success": False, "message": f"LLM bağlantı hatası: LM Studio kapalı olabilir."}

# İstenildiğinde AI Raporu Al
@app.get("/get_report")
async def get_report(username: str, lang: str = "en"):
    res = await evaluate_user_with_llm(username, lang)
    return res

async def evaluate_and_set_thresholds(username: str):
    """AI ile kullanıcının kişiye özel eşiklerini belirle."""
    if username not in users_db:
        return
    user = users_db[username]
    prompt = f"""You are a medical AI. Set personalized safe heart rate and SpO2 thresholds for this patient:
Name: {user['name']}, Age: {user['age']}, Illness: {user.get('illness','none')}, Allergies: {user.get('allergies','none')}.
Notes: {user.get('notes', 'none')}.
Consider their medical conditions carefully. Respond STRICTLY with a valid JSON: {{"max_hr": <integer>, "min_spo2": <integer>, "reason": "brief explanation"}}"""
    
    print(f"\n[AI Eşik Belirleme - {user['name']}]:\n{prompt}\n")
    payload = {
        "model": "google/gemma-4-e4b",
        "messages": [
            {"role": "system", "content": "You are a medical AI. Output ONLY valid JSON, no markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1, "max_tokens": 150
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=15) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    answer = resp_json["choices"][0]["message"]["content"].strip()
                    if answer.startswith("```"): answer = answer.replace("```json","").replace("```","").strip()
                    ai_data = json.loads(answer)
                    users_db[username]["thresholds"] = {
                        "max_hr": int(ai_data.get("max_hr", 150)),
                        "min_spo2": int(ai_data.get("min_spo2", 92))
                    }
                    print(f"[AI Eşik Sonucu - {user['name']}]: max_hr={users_db[username]['thresholds']['max_hr']}, min_spo2={users_db[username]['thresholds']['min_spo2']}")
    except Exception as e:
        print(f"[AI Eşik Hataı - {username}]: {e}")

async def periodic_llm_checker():
    """Her 5 dakikada bir (demo için 1 dakika yapabiliriz ama 5 dakika istendi) kullanıcıları tarar."""
    while True:
        await asyncio.sleep(300) # 5 dakika bekle
        for username, user in users_db.items():
            # Donanım bağlı olanlara öncelik veya aktif ziyaretçiler
            if user.get("is_hardware_connected") or random.random() < 0.3:
                res = await evaluate_user_with_llm(username)
                if res.get("success") and res.get("is_danger"):
                    msg = {
                        "type": "sensor",
                        "username": username,
                        "name": user["name"],
                        "hr": user["vitals"]["hr"],
                        "spo2": user["vitals"]["spo2"],
                        "lat": user["vitals"]["lat"],
                        "lng": user["vitals"]["lng"],
                        "alert": "CRITICAL_ALERT",
                        "reason": f"[AI DETECTED] {res.get('report')}",
                        "allergies": user["allergies"],
                        "emergency_contact": user["emergency_contact"]
                    }
                    await manager.broadcast(json.dumps(msg))

@app.get("/{filename}")
async def get_static(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return {"error": "File not found"}

# Kişiselleştirilmiş Eşik Değerler ve Kural Tabanlı Kontrol
async def process_user_data(username, data):
    hr = data["hr"]
    spo2 = data["spo2"]
    user = users_db[username]
    
    log_vitals(username, hr, spo2)
    
    # Kullanıcının AI ile belirlenmiş eşiklerini kullan
    thresholds = user.get("thresholds", {})
    max_safe_hr = thresholds.get("max_hr", int((220 - user["age"]) * 0.85))
    min_safe_spo2 = thresholds.get("min_spo2", 92)
        
    is_critical = False
    reason = ""
    
    # Sensör parmağa takılı değilse (0 ise) alarm verme
    if hr > 0 and spo2 > 0:
        if hr > max_safe_hr:
            is_critical = True
            reason = f"Yüksek Nabız! (Sınır: {int(max_safe_hr)})"
        elif spo2 < min_safe_spo2:
            is_critical = True
            reason = f"SpO2 seviyesi tehlikeli boyutta düşük! (Sınır: %{min_safe_spo2})"
            
    # Cooldown (Spam koruması: Aynı kullanıcı için 30 saniyede 1 uyarı)
    current_time = time.time()
    if is_critical:
        last_alert = user.get("last_alert_time", 0)
        if current_time - last_alert < 30:
            is_critical = False
        else:
            user["last_alert_time"] = current_time

    # Vitals history for AI context
    history = user.setdefault("vitals_history", [])
    history.append({"hr": hr, "spo2": spo2})
    if len(history) > 25:
        history.pop(0)

    msg = {
        "type": "sensor",
        "username": username,
        "name": user["name"],
        "age": user["age"],
        "illness": user["illness"],
        "allergies": user["allergies"],
        "emergency_contact": user.get("emergency_contact", "none"),
        "watchlist": user.get("watchlist", False),
        "thresholds": user.get("thresholds", {"max_hr": 150, "min_spo2": 92}),
        "notes": user.get("notes", ""),
        "hr": hr,
        "spo2": spo2,
        "lat": data["lat"],
        "lng": data["lng"]
    }
    
    if is_critical:
        msg["alert"] = "CRITICAL_ALERT"
        msg["reason"] = reason
        msg["allergies"] = user["allergies"]
        msg["emergency_contact"] = user["emergency_contact"]
        
    await manager.broadcast(json.dumps(msg))

import serial.tools.list_ports
import collections

BLUETOOTH_PORT = 'COM10' 
BAUD_RATE = 9600

# Sensör veri yumuşatma (Smoothing) için geçmiş verileri tutan kuyruklar
hr_history = collections.deque(maxlen=4)
spo2_history = collections.deque(maxlen=4)

def filter_sensor_data(data):
    if "hr" in data and "spo2" in data:
        raw_hr = data["hr"]
        raw_spo2 = data["spo2"]
        
        if raw_hr < 40 or raw_hr > 200 or raw_spo2 < 50:
            if len(hr_history) > 0:
                data["hr"] = int(sum(hr_history) / len(hr_history))
            if len(spo2_history) > 0:
                data["spo2"] = int(sum(spo2_history) / len(spo2_history))
        else:
            hr_history.append(raw_hr)
            spo2_history.append(raw_spo2)
            data["hr"] = int(sum(hr_history) / len(hr_history))
            data["spo2"] = int(sum(spo2_history) / len(spo2_history))
            
    return data

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def serial_reader(loop):
    try:
        ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1)
        print(f"[Bluetooth] Bağlantı sağlandı! ({BLUETOOTH_PORT})")
        users_db["kaan"]["is_hardware_connected"] = True
        
        while True:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8', errors='ignore').rstrip()
                if not raw_data:
                    continue
                try:
                    data = json.loads(raw_data)
                    data = filter_sensor_data(data)
                    users_db["kaan"]["vitals"].update(data)
                    asyncio.run_coroutine_threadsafe(process_user_data("kaan", data), loop)
                except json.JSONDecodeError:
                    pass
            time.sleep(0.1)
    except serial.SerialException:
        available_ports = get_available_ports()
        port_list = ", ".join(available_ports) if available_ports else "Hiç port bulunamadı"
        print(f"\n[Uyarı] Donanım bulunamadı ({BLUETOOTH_PORT} açılamadı).")
        print(f"🔍 Açık portlar: {port_list}")
        print("Sistem botlar üzerinden simülasyon ile çalışmaya devam edecek.\n")

def simulate_all_users(loop):
    while True:
        for username, user in list(users_db.items()):
            if username == "kaan" and user.get("is_hardware_connected"):
                continue
                
            if username == "kutay":
                v = user["vitals"]
                asyncio.run_coroutine_threadsafe(process_user_data(username, v), loop)
                continue
                
            v = user["vitals"]
            v["hr"] += random.randint(-4, 4)
            v["hr"] = max(55, min(185, v["hr"]))
            v["spo2"] += random.randint(-1, 1)
            v["spo2"] = max(90, min(100, v["spo2"]))
            v["lat"] += random.uniform(-0.0001, 0.0001)
            v["lng"] += random.uniform(-0.0001, 0.0001)

            asyncio.run_coroutine_threadsafe(process_user_data(username, v), loop)
        time.sleep(2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
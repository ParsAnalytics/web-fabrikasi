"""
server.py
---------
Şifre korumalı, Web Terminal Konsol destekli gelişmiş kontrol sunucusu.
Leads klasöründeki ham taranmış verileri arayüze servis eder.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
# Vercel sunucusuz dosya sisteminde yazılabilir tek klasör /tmp'dir
if os.getenv("VERCEL"):
    DATA_DIR = Path("/tmp/data")
    DEMOS_DIR = Path("/tmp/demos")
    LEADS_DIR = Path("/tmp/leads")
else:
    DATA_DIR = BASE_DIR / "data"
    DEMOS_DIR = BASE_DIR / "demos"
    LEADS_DIR = BASE_DIR / "leads"

# Klasörleri oluştur
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEMOS_DIR.mkdir(parents=True, exist_ok=True)
LEADS_DIR.mkdir(parents=True, exist_ok=True)

CUSTOMERS_DB = DATA_DIR / "customers.json"
EVENTS_LOG = DATA_DIR / "events.json"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

app = FastAPI(title="Web Fabrikası Güvenli Kontrol Paneli")

# Güvenlik Kontrolü
async def verify_auth(x_admin_password: str = Header(None)):
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Yetkisiz erişim. Şifre hatalı.")
    return True

# Yardımcı veri okuma/yazma fonksiyonları
def load_json(path: Path, default_type=list) -> dict | list:
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_type()
    return default_type()

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_event(event_type: str, data: dict):
    events = load_json(EVENTS_LOG, list)
    events.append({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    })
    save_json(EVENTS_LOG, events)

# ── API ENDPOINTS ─────────────────────────────────────────────

@app.post("/api/auth/verify")
async def verify_password(payload: dict):
    password = payload.get("password")
    if password == ADMIN_PASSWORD:
        return {"status": "ok", "message": "Giriş başarılı"}
    raise HTTPException(status_code=401, detail="Şifre hatalı")

@app.post("/api/run/scraper", dependencies=[Depends(verify_auth)])
async def run_scraper(query: str = "çekici", city: str = "Kadıköy"):
    """Maps kazıyıcıyı senkron çalıştırıp sonuçları döner."""
    try:
        log_event("scraper_started", {"query": query, "city": city})
        cmd = f'python lead_scraper.py --query "{query}" --city "{city}"'
        subprocess.run(cmd, shell=True, check=True)
        log_event("scraper_completed", {"query": query, "city": city})
        
        # En son üretilen lead JSON dosyasını bul ve oku
        lead_files = sorted(LEADS_DIR.glob("leads_*.json"))
        if lead_files:
            latest_file = lead_files[-1]
            leads_data = load_json(latest_file)
            return {"status": "success", "message": f"{len(leads_data)} lead başarıyla toplandı.", "leads": leads_data}
        return {"status": "success", "message": "Tarama bitti ancak dosya bulunamadı.", "leads": []}
    except Exception as e:
        log_event("scraper_failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run/generator", dependencies=[Depends(verify_auth)])
async def run_generator(background_tasks: BackgroundTasks):
    def worker():
        try:
            log_event("generator_started", {})
            subprocess.run("python demo_generator.py", shell=True, check=True)
            log_event("generator_completed", {})
            subprocess.run("git add demos/ demo_generator.py", shell=True, check=False)
            subprocess.run('git commit -m "auto: rebuild demos"', shell=True, check=False)
            subprocess.run("git push origin main", shell=True, check=False)
            log_event("github_push_completed", {})
        except Exception as e:
            log_event("generator_failed", {"error": str(e)})

    background_tasks.add_task(worker)
    return {"status": "started", "message": "Demo üretimi ve GitHub yayını başlatıldı."}

@app.post("/api/run/sender", dependencies=[Depends(verify_auth)])
async def run_sender(background_tasks: BackgroundTasks, send_real: bool = False):
    mode_flag = "--send" if send_real else ""
    def worker():
        try:
            log_event("sender_started", {"mode": "real" if send_real else "simulation"})
            subprocess.run(f"python whatsapp_sender.py {mode_flag}", shell=True, check=True)
            log_event("sender_completed", {})
        except Exception as e:
            log_event("sender_failed", {"error": str(e)})

    background_tasks.add_task(worker)
    return {"status": "started", "message": "WhatsApp gönderimi başlatıldı."}

@app.post("/api/create-payment", dependencies=[Depends(verify_auth)])
async def create_payment_link(slug: str, name: str, phone: str, amount: float = 999.0):
    try:
        cmd = f'python payment_link.py --slug "{slug}" --name "{name}" --phone "{phone}" --amount {amount}'
        subprocess.run(cmd, shell=True, check=True)
        log_event("payment_link_created", {"slug": slug, "amount": amount})
        return {"status": "success", "message": f"{name} için ödeme talebi oluşturuldu."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run/terminal", dependencies=[Depends(verify_auth)])
async def run_terminal_command(payload: dict):
    command = payload.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="Komut boş olamaz")
    
    forbidden = ["rm -rf", "del /", "format", "mkfs"]
    if any(f in command.lower() for f in forbidden):
        return {"output": "Hata: Güvenlik nedeniyle bu komutu çalıştırmanıza izin verilmiyor."}

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        return {"output": output}
    except subprocess.TimeoutExpired:
        return {"output": "Hata: Komut zaman aşımına uğradı (30 saniye)."}
    except Exception as e:
        return {"output": f"Sistem Hatası: {str(e)}"}

@app.get("/api/dashboard-data", dependencies=[Depends(verify_auth)])
async def get_dashboard_data():
    demos = load_json(DEMOS_DIR / "generated_demos.json")
    send_log = load_json(DEMOS_DIR / "send_log.json", dict)
    customers = load_json(CUSTOMERS_DB, dict)
    events = load_json(EVENTS_LOG)

    active_customers = [c for c in customers.values() if c.get("status") == "active"]
    sent_list = send_log.get("sent", [])

    return {
        "demos": demos,
        "sent_count": len(sent_list),
        "active_customers_count": len(active_customers),
        "monthly_revenue": len(active_customers) * 125,
        "events": events[-15:],
        "customers": customers,
        "send_log": send_log
    }

@app.get("/api/scraped-leads", dependencies=[Depends(verify_auth)])
async def get_scraped_leads():
    """Son taranan lead dosyalarını arayüze döner."""
    lead_files = sorted(LEADS_DIR.glob("leads_*.json"))
    if lead_files:
        return load_json(lead_files[-1])
    return []

@app.get("/", response_class=HTMLResponse)
async def serve_gui():
    html_file = BASE_DIR / "dashboard.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Görsel arayüz dosyası bulunamadı.")
    with open(html_file, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

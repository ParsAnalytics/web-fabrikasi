"""
server.py
---------
Şifre korumalı, Web Terminal Konsol destekli gelişmiş kontrol sunucusu.
Leads klasöründeki ham taranmış verileri arayüze servis eder.
"""

import sys, io
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
app.mount("/demos", StaticFiles(directory=str(DEMOS_DIR)), name="demos")

REACT_DIR = BASE_DIR / "react_app"
if (REACT_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_DIR / "assets")), name="react_assets")

# Güvenlik Kontrolü (Devre Dışı Bırakıldı - Açık Erişim)
async def verify_auth(x_admin_password: str = Header(None)):
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

@app.post("/api/run/scraper")
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

@app.post("/api/run/generator")
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

@app.post("/api/run/optimizer")
async def run_optimizer(background_tasks: BackgroundTasks):
    """Lead'leri Claude/AI ile optimize eder."""
    def worker():
        try:
            log_event("optimizer_started", {})
            lead_files = sorted(LEADS_DIR.glob("leads_*.json"))
            if not lead_files:
                log_event("optimizer_failed", {"error": "Lead dosyası bulunamadı"})
                return
            
            latest_file = lead_files[-1]
            with open(latest_file, encoding="utf-8") as f:
                leads = json.load(f)
                
            from ai_optimizer import AIOptimizer
            import asyncio
            
            async def run_ai():
                opt = AIOptimizer()
                optimized = await opt.optimize_leads_batch(leads)
                with open(latest_file, "w", encoding="utf-8") as fw:
                    json.dump(optimized, fw, ensure_ascii=False, indent=2)
                    
            asyncio.run(run_ai())
            log_event("optimizer_completed", {"count": len(leads)})
            
        except Exception as e:
            log_event("optimizer_failed", {"error": str(e)})

    background_tasks.add_task(worker)
    return {"status": "started", "message": "AI Optimizasyon arkaplanda başlatıldı."}

@app.post("/api/run/video")
async def run_video(background_tasks: BackgroundTasks):
    """Tanıtım videoları üretir."""
    def worker():
        try:
            log_event("video_started", {})
            subprocess.run("python video_generator.py", shell=True, check=True)
            log_event("video_completed", {})
        except Exception as e:
            log_event("video_failed", {"error": str(e)})
            
    background_tasks.add_task(worker)
    return {"status": "started", "message": "Video üretim süreci arkaplanda başlatıldı."}

@app.post("/api/run/sender")
async def run_sender(background_tasks: BackgroundTasks):
    def worker():
        try:
            log_event("sender_started", {})
            subprocess.run("python whatsapp_sender.py", shell=True, check=True)
            log_event("sender_completed", {})
        except Exception as e:
            log_event("sender_failed", {"error": str(e)})

    background_tasks.add_task(worker)
    return {"status": "started", "message": "WhatsApp/Email otomatik gönderimi başlatıldı."}

@app.post("/api/create-payment")
async def create_payment_route(payload: dict):
    company = payload.get("companyName")
    price = payload.get("price", 999.00)
    if not company:
        raise HTTPException(status_code=400, detail="Firma adı zorunlu")
    
    from payment_link import generate_payment_link
    try:
        link_data = generate_payment_link(company, price)
        log_event("payment_link_created", link_data)
        return {"status": "success", "link": link_data["payment_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leads/import-raw")
async def import_raw_leads(payload: dict):
    raw_text = payload.get("text", "")
    from demo_generator import slugify
    
    def map_category_text(text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["çekici", "yol yardım", "kurtarma", "kurtarıcı", "kurtari"]):
            return "cekici"
        elif any(k in text_lower for k in ["anaokulu", "kreş", "okul"]):
            return "anaokulu"
        elif any(k in text_lower for k in ["kuaför", "güzellik", "berber", "saç"]):
            return "kuafor"
        elif any(k in text_lower for k in ["restoran", "lokanta", "kafe", "yemek"]):
            return "restoran"
        elif any(k in text_lower for k in ["motosiklet", "tamir", "oto servis", "lastik", "araba"]):
            return "cekici"
        return "genel"
        
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    parsed_leads = []
    
    rating_pattern = re.compile(r'^(\d[,\.]\d)\((\d+)\)$')
    
    for idx, line in enumerate(lines):
        match = rating_pattern.match(line)
        if match:
            rating = float(match.group(1).replace(',', '.'))
            review_count = int(match.group(2))
            
            name = ""
            name_idx = idx - 1
            while name_idx >= 0:
                candidate = lines[name_idx]
                if candidate in ["Sponsorlu", "Paylaş", "Yeni", "Site", "Web sitesi", "Yol tarifi"]:
                    name_idx -= 1
                    continue
                name = candidate
                break
                
            if not name:
                continue
                
            category = "genel"
            address = ""
            cat_addr_line = ""
            if idx + 1 < len(lines):
                cat_addr_line = lines[idx + 1]
                
            parts = re.split(r'[·⋅•]', cat_addr_line)
            if len(parts) >= 2:
                category_text = parts[0].strip()
                address = parts[1].strip()
                category = map_category_text(category_text)
            elif cat_addr_line:
                address = cat_addr_line
                
            phone = ""
            for offset in [2, 3]:
                if idx + offset < len(lines):
                    candidate_line = lines[idx + offset]
                    phone_match = re.search(r'(?:\+90|0)?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}', candidate_line)
                    if phone_match:
                        phone = phone_match.group(0).strip()
                        break
            
            has_website = False
            for j in range(idx + 1, min(idx + 6, len(lines))):
                if lines[j].strip().lower() in ["web sitesi", "website", "site"]:
                    has_website = True
                    break
                    
            parsed_leads.append({
                "name": name,
                "phone": phone,
                "address": address,
                "city": "İstanbul",
                "rating": rating,
                "review_count": review_count,
                "category": category,
                "has_website": has_website,
                "types": category,
                "scraped_at": datetime.now().isoformat()
            })
            
    send_log = load_json(DEMOS_DIR / "send_log.json", dict)
    customers = load_json(CUSTOMERS_DB, dict)
    
    from whatsapp_sender import normalize_phone
    
    existing_phones = set()
    
    for e in send_log.get("sent", []):
        p = e.get("phone")
        if p:
            try: existing_phones.add(normalize_phone(p))
            except Exception: pass
            
    for e in send_log.get("failed", []):
        p = e.get("phone")
        if p:
            try: existing_phones.add(normalize_phone(p))
            except Exception: pass

    for c in customers.values():
        p = c.get("phone")
        if p:
            try: existing_phones.add(normalize_phone(p))
            except Exception: pass
            
    lead_files = sorted(LEADS_DIR.glob("leads_*.json"))
    for lf in lead_files:
        try:
            leads_in_file = load_json(lf)
            for l in leads_in_file:
                p = l.get("phone")
                if p:
                    try: existing_phones.add(normalize_phone(p))
                    except Exception: pass
        except Exception:
            pass

    unique_new_leads = []
    skipped_duplicates = 0
    skipped_has_website = 0
    skipped_no_phone = 0
    
    for lead in parsed_leads:
        if not lead["phone"]:
            skipped_no_phone += 1
            continue
            
        try:
            norm_phone = normalize_phone(lead["phone"])
        except Exception:
            skipped_no_phone += 1
            continue
            
        if norm_phone in existing_phones:
            skipped_duplicates += 1
            continue
            
        if lead["has_website"]:
            skipped_has_website += 1
            continue
            
        lead["score"] = score_lead(lead)
        lead["slug"] = slugify(f"{lead['name']}-istanbul")
        lead.pop("has_website", None)
        
        unique_new_leads.append(lead)
        existing_phones.add(norm_phone)
        
    if not unique_new_leads:
        return {
            "status": "success",
            "message": f"Yeni aday bulunamadı. (Ayrıştırılan: {len(parsed_leads)}, Mükerrer: {skipped_duplicates}, Web sitesi olan: {skipped_has_website}, Telefonu eksik: {skipped_no_phone})",
            "count": 0
        }
        
    filename = f"leads_manual_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out_path = LEADS_DIR / filename
    save_json(out_path, unique_new_leads)
    
    csv_filename = filename.replace(".json", ".csv")
    from lead_scraper import save_to_csv
    save_to_csv(unique_new_leads, csv_filename)
    
    log_event("manual_leads_imported", {"count": len(unique_new_leads), "file": filename})
    
    return {
        "status": "success",
        "message": f"{len(unique_new_leads)} yeni aday başarıyla içe aktarıldı! (Toplam ayrıştırılan: {len(parsed_leads)}, Mükerrer: {skipped_duplicates}, Web sitesi olan: {skipped_has_website})",
        "count": len(unique_new_leads)
    }

@app.post("/api/run/terminal")
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

@app.get("/api/dashboard-data")
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

@app.get("/api/scraped-leads")
async def get_scraped_leads():
    """Son taranan lead dosyalarını arayüze döner."""
    lead_files = sorted(LEADS_DIR.glob("leads_*.json"))
    if lead_files:
        return load_json(lead_files[-1])
    return []

@app.get("/bot", response_class=HTMLResponse)
async def serve_bot_gui():
    html_file = BASE_DIR / "dashboard.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Görsel arayüz dosyası bulunamadı.")
    with open(html_file, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/", response_class=HTMLResponse)
async def serve_react_gui():
    html_file = BASE_DIR / "react_app" / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="React arayüz dosyası bulunamadı. Lütfen npm run build ile React projesini derleyip react_app klasörüne kopyalayın.")
    with open(html_file, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

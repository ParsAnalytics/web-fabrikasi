"""
webhook_server.py
-----------------
FastAPI tabanlı webhook sunucusu.

Görevleri:
  1. Demo sayfa tıklama takibi  → /track/{slug}
  2. iyzico ödeme callback'i   → /payment/success
  3. Yenileme zamanlayıcısı    → arka planda çalışır
  4. Slack bildirimleri        → satış ve tıklama olayları

Çalıştırma:
  pip install fastapi uvicorn apscheduler requests python-dotenv
  python webhook_server.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("[!] apscheduler bulunamadı. pip install apscheduler")

# ── AYARLAR ────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DEMOS_DIR     = BASE_DIR / "demos"
CUSTOMERS_DB  = BASE_DIR / "data" / "customers.json"
EVENTS_LOG    = BASE_DIR / "data" / "events.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
PORT          = int(os.getenv("WEBHOOK_PORT", 8080))

app = FastAPI(title="Web Fabrikası Webhook", version="1.0.0")


# ── VERİ YARDIMCILARI ──────────────────────────────────────
def load_json(path: Path) -> dict | list:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {} if path.suffix == ".json" and "customers" in path.name else []


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_event(event_type: str, data: dict):
    events = load_json(EVENTS_LOG)
    if not isinstance(events, list):
        events = []
    events.append({
        "type":      event_type,
        "data":      data,
        "timestamp": datetime.now().isoformat(),
    })
    save_json(EVENTS_LOG, events)


# ── SLACK BİLDİRİMİ ───────────────────────────────────────
def notify_slack(message: str):
    if not SLACK_WEBHOOK:
        print(f"[SLACK] {message}")
        return
    try:
        import requests
        requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
    except Exception as e:
        print(f"[!] Slack hatası: {e}")


# ── DEMO SUNUCU ────────────────────────────────────────────
@app.get("/demos/{slug}", response_class=HTMLResponse)
@app.get("/demos/{slug}/", response_class=HTMLResponse)
async def serve_demo(slug: str, request: Request):
    """Demo sayfasını sun ve tıklamayı kaydet."""
    html_file = DEMOS_DIR / slug / "index.html"

    if not html_file.exists():
        raise HTTPException(status_code=404, detail=f"Demo bulunamadı: {slug}")

    # Tıklama olayını kaydet
    log_event("demo_viewed", {
        "slug": slug,
        "ip":   request.client.host,
        "ua":   request.headers.get("user-agent", ""),
    })

    notify_slack(f"👀 Demo görüntülendi: *{slug}*")

    with open(html_file, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── ÖDEME CALLBACK ─────────────────────────────────────────
@app.post("/payment/success")
async def payment_success(request: Request):
    """iyzico ödeme başarılı callback'i."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        try:
            body = dict(await request.form())
        except Exception:
            body = {}

    # Query parametrelerini de ekle (GET istekleri veya url-encoded fallback'ler için)
    params = dict(request.query_params)
    for k, v in params.items():
        if k not in body or not body[k]:
            body[k] = v

    slug        = body.get("conversationId", body.get("slug", ""))
    amount      = body.get("price", 0)
    customer_ph = body.get("buyerGsmNumber", "")

    if not slug:
        raise HTTPException(status_code=400, detail="slug eksik")

    # Müşteri kaydı oluştur
    customers = load_json(CUSTOMERS_DB)
    if not isinstance(customers, dict):
        customers = {}

    customers[slug] = {
        "slug":       slug,
        "phone":      customer_ph,
        "amount":     amount,
        "paid_at":    datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
        "status":     "active",
    }
    save_json(CUSTOMERS_DB, customers)

    # Siteyi aktive et
    activate_site(slug)

    # Bildirimleri gönder
    log_event("payment_received", {"slug": slug, "amount": amount})
    notify_slack(f"💰 *YENİ SATIŞ!* `{slug}` — {amount} ₺")

    return JSONResponse({"status": "ok", "message": f"{slug} aktive edildi"})


@app.get("/payment/success")
async def payment_success_redirect(request: Request):
    """iyzico bazen GET ile de callback yapar."""
    params = dict(request.query_params)
    slug   = params.get("conversationId", params.get("slug", ""))
    if slug:
        await payment_success(request)
    return RedirectResponse(url=f"/demos/{slug}/tesekkurler")


# ── SİTE AKTİVASYON ────────────────────────────────────────
def activate_site(slug: str):
    """Ödeme gelince siteyi aktive et."""
    print(f"\n[AKTİF] {slug} aktive ediliyor...")

    # 1. Demo'dan gerçek siteye kopyala (şimdilik aynı klasör)
    demo_path = DEMOS_DIR / slug / "index.html"
    if not demo_path.exists():
        print(f"  [!] Demo bulunamadı: {demo_path}")
        return

    # 2. "DEMO" banner'ını kaldır (canlı versiyonda satın alma uyarısı olmayacak)
    with open(demo_path, encoding="utf-8") as f:
        html = f.read()

    # Purchase banner'ı gizle
    html = html.replace(
        'class="purchase-banner"',
        'class="purchase-banner" style="display:none"'
    )

    live_path = DEMOS_DIR / slug / "live.html"
    with open(live_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✅ Canlı versiyon: {live_path}")

    # 3. Müşteriye WhatsApp teslim mesajı gönder (isteğe bağlı)
    customers = load_json(CUSTOMERS_DB)
    customer  = customers.get(slug, {})
    if customer.get("phone"):
        send_delivery_message(slug, customer["phone"])


def send_delivery_message(slug: str, phone: str):
    """Müşteriye sitenin hazır olduğunu WhatsApp ile bildir."""
    msg = f"""✅ Siteniz hazır!

Merhaba, web siteniz yayına alındı. 

🔗 Siteniz: https://demo.webfabrika.com.tr/{slug}/

Herhangi bir sorun veya değişiklik için bize yazabilirsiniz.

— Web Fabrikası Ekibi"""
    print(f"  [WA] Teslim mesajı: {phone}")
    # Burada gerçek WhatsApp gönderimi yapılır (whatsapp_sender.py)


# ── YENİLEME KONTROLÜ ──────────────────────────────────────
def check_renewals():
    """Her gün sabah 9'da çalışır. Süresi yaklaşan müşterileri uyar."""
    customers = load_json(CUSTOMERS_DB)
    if not isinstance(customers, dict):
        return

    now = datetime.now()
    for slug, customer in customers.items():
        if customer.get("status") != "active":
            continue

        expires = datetime.fromisoformat(customer["expires_at"])
        days_left = (expires - now).days

        phone = customer.get("phone", "")
        if not phone:
            continue

        if days_left == 30:
            msg = f"📅 Sitenizin aboneliği 30 gün içinde dolacak. Yenilemek için bize yazın."
            notify_slack(f"📅 Yenileme hatırlatması: `{slug}` — 30 gün kaldı")
        elif days_left == 7:
            msg = f"⚠️ Sitenizin aboneliği 7 gün içinde dolacak! Yenilememe halinde site askıya alınır."
            notify_slack(f"⚠️ Yenileme acil: `{slug}` — 7 gün kaldı")
        elif days_left == 1:
            msg = f"🚨 Sitenizin aboneliği YARIN doluyor. Hemen yenileyin!"
            notify_slack(f"🚨 YARIN doluyor: `{slug}`")
        elif days_left < 0:
            # Siteyi askıya al
            customers[slug]["status"] = "suspended"
            save_json(CUSTOMERS_DB, customers)
            notify_slack(f"⛔ Site askıya alındı: `{slug}` (ödeme yapılmadı)")
            print(f"  [ASKIYA] {slug} askıya alındı.")
            continue
        else:
            continue

        print(f"  [YENİLEME] {slug}: {days_left} gün kaldı → WA mesajı gönderiliyor")
        log_event("renewal_reminder", {"slug": slug, "days_left": days_left, "phone": phone})


# ── ZAMANLAYICI ────────────────────────────────────────────
if SCHEDULER_AVAILABLE:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_renewals, "cron", hour=9, minute=0)


# ── STATUS ENDPOINT ────────────────────────────────────────
@app.get("/status")
async def status():
    """Sistem sağlık kontrolü."""
    customers = load_json(CUSTOMERS_DB)
    events    = load_json(EVENTS_LOG)

    active    = sum(1 for c in (customers.values() if isinstance(customers, dict) else []) if c.get("status") == "active")
    suspended = sum(1 for c in (customers.values() if isinstance(customers, dict) else []) if c.get("status") == "suspended")

    return {
        "status":           "ok",
        "timestamp":        datetime.now().isoformat(),
        "customers_active": active,
        "customers_suspended": suspended,
        "total_events":     len(events) if isinstance(events, list) else 0,
    }


@app.get("/customers")
async def list_customers():
    """Aktif müşteri listesi."""
    customers = load_json(CUSTOMERS_DB)
    return customers


# ── STARTUP ────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print(f"\n{'='*50}")
    print(f"  Web Fabrikası Webhook Sunucusu")
    print(f"  Port    : {PORT}")
    print(f"  Status  : http://localhost:{PORT}/status")
    print(f"  Demolar : http://localhost:{PORT}/demos/{{slug}}")
    print(f"{'='*50}\n")

    if SCHEDULER_AVAILABLE:
        scheduler.start()
        print("  Yenileme zamanlayıcısı başlatıldı (her gün 09:00)")


# ── ANA ÇALIŞMA ────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "webhook_server:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info",
    )

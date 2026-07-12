"""
whatsapp_sender.py
------------------
generated_demos.json'daki leadlere WhatsApp mesaji gonderir.

Mod 1 — Simülasyon (varsayılan, API gerekmez):
  python whatsapp_sender.py

Mod 2 — Twilio ile gerçek gönderim:
  python whatsapp_sender.py --send

Mod 3 — Belirli bir leade test mesajı:
  python whatsapp_sender.py --test 05321234567
"""

import sys, io
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import json
import time
import random
import argparse
from pathlib import Path
from datetime import datetime

# ── AYARLAR ────────────────────────────────────────────────────────────────

DEMOS_JSON    = Path(__file__).parent / "demos" / "generated_demos.json"
LOG_FILE      = Path(__file__).parent / "demos" / "send_log.json"

# Twilio ayarları (gerçek gönderim için .env dosyasına koy)
TWILIO_SID    = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WA_NUM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Anti-spam: mesajlar arası bekleme süresi (saniye)
WAIT_MIN = 35
WAIT_MAX = 90

# Günlük maksimum gönderim
DAILY_LIMIT = 50


# ── MESAJ ŞABLONU ──────────────────────────────────────────────────────────

def build_message(lead: dict) -> str:
    """
    Kişiselleştirilmiş WhatsApp mesajı üret.
    Her mesaj biraz farklı olsun — spam filtrelerini atlatmak için.
    """
    name       = lead["name"]
    first_word = name.split()[0]   # "Karadeniz Yol Yardım" → "Karadeniz"
    demo_url   = lead["demo_url"]

    # A/B test için birden fazla varyant — rastgele seç
    variants = [
        f"""Merhaba {first_word} 👋

Google Haritalar'da {name} işletmenizi inceledim ve müşterilerinizin sizi daha kolay bulabilmesi için özel bir web sitesi hazırladım:

🔗 {demo_url}

Araç arıyan sürücüler önce Google'a bakıyor — web siteniz yoksa rakiplerinize gidiyorlar. Kurulum tek seferlik 999 ₺ + 125 ₺/ay bakım.

İnceleyip düşüncelerinizi yazarsanız sevinirim 🙂""",

        f"""Merhaba, {name} yetkilisi!

Yol yardım ve çekici hizmetleri arayanlarda Google ilk tercihtir. Sitenizin olmadığını fark edince size özel hazırladım:

👉 {demo_url}

Beğenirseniz 999 ₺'ye siteniz hazır ve canlıda. Sormak istediğiniz bir şey varsa yazın.""",

        f"""Selam {first_word} Bey/Hanım,

Kadıköy bölgesinde çekici/yol yardım arayanların büyük çoğunluğu Google'dan geliyor. Web siteniz olmadığı için bu müşterileri kaçırıyorsunuz.

Sizin için hazırladığım demo:
🔗 {demo_url}

30 saniye bakın, beğenirseniz konuşuruz. Kurulum 999 ₺.""",
    ]

    return random.choice(variants)


# ── TELEFON FORMATLAMA ─────────────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """
    'Hızır Oto' lead'inden gelen çeşitli formatlara göre normalleştir.
    Çıktı: 'whatsapp:+905321112233'
    """
    digits = "".join(filter(str.isdigit, phone))

    # Başındaki 0'ı at, 90 ekle
    if digits.startswith("90"):
        pass
    elif digits.startswith("0"):
        digits = "90" + digits[1:]
    else:
        digits = "90" + digits

    # Minimum 12 hane olmalı (905xxxxxxxxx)
    if len(digits) < 12:
        raise ValueError(f"Geçersiz telefon: {phone} → {digits}")

    return f"whatsapp:+{digits}"


# ── LOG YÖNETIMI ───────────────────────────────────────────────────────────

def load_log() -> dict:
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"sent": [], "failed": [], "skipped": []}


def save_log(log: dict):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def already_sent(log: dict, slug: str, phone: str = None) -> bool:
    if any(e.get("slug") == slug for e in log["sent"]):
        return True
    if phone:
        try:
            norm_phone = normalize_phone(phone)
            for e in log["sent"]:
                log_phone = e.get("phone")
                if log_phone:
                    try:
                        if normalize_phone(log_phone) == norm_phone:
                            return True
                    except Exception:
                        pass
        except Exception:
            pass
    return False


def count_today(log: dict) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(1 for e in log["sent"] if e.get("date", "").startswith(today))


# ── GÖNDERIM FONKSİYONLARI ────────────────────────────────────────────────

def send_via_twilio(to: str, body: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            from_=TWILIO_WA_NUM,
            to=to,
            body=body
        )
        print(f"     SID: {msg.sid}")
        return True
    except ImportError:
        print("     [!] twilio paketi yüklü değil: pip install twilio")
        return False
    except Exception as e:
        print(f"     [!] Twilio hatası: {e}")
        return False


def simulate_send(to: str, body: str, lead_name: str) -> bool:
    """Gerçek gönderim yerine mesajı terminale yaz."""
    print(f"\n{'─'*60}")
    print(f"  ALICI : {to}")
    print(f"  MESAJ :\n")
    for line in body.splitlines():
        print(f"    {line}")
    print(f"{'─'*60}")
    return True


# ── ANA GÖNDERIM DÖNGÜSÜ ───────────────────────────────────────────────────

def run(send_real: bool = False, test_phone: str = None):
    if not DEMOS_JSON.exists():
        print(f"[!] {DEMOS_JSON} bulunamadı. Önce demo_generator.py çalıştırın.")
        return

    with open(DEMOS_JSON, encoding="utf-8") as f:
        leads = json.load(f)

    log = load_log()

    # Test modu: sadece belirtilen numaraya gönder
    if test_phone:
        lead = leads[0]
        msg  = build_message(lead)
        to   = normalize_phone(test_phone)
        print(f"\n[TEST] {to} numarasına gönderiliyor...\n")
        if send_real:
            send_via_twilio(to, msg)
        else:
            simulate_send(to, msg, lead["name"])
        return

    # Günlük limit kontrolü
    sent_today = count_today(log)
    if sent_today >= DAILY_LIMIT:
        print(f"[!] Günlük limit doldu ({sent_today}/{DAILY_LIMIT}). Yarın devam edin.")
        return

    print(f"\n{'='*60}")
    print(f"  WhatsApp Gönderim Başlıyor")
    print(f"  Toplam lead : {len(leads)}")
    print(f"  Bugün gönderilen: {sent_today}/{DAILY_LIMIT}")
    print(f"  Mod: {'GERÇEK (Twilio)' if send_real else 'SİMÜLASYON'}")
    print(f"{'='*60}\n")

    sent_count = 0

    for i, lead in enumerate(leads, 1):
        slug = lead.get("slug", lead["name"])

        # Daha önce gönderildi mi?
        if already_sent(log, slug, lead.get("phone")):
            print(f"  [{i:02d}] ATLA  | {lead['name']} (zaten gönderildi)")
            log["skipped"].append({"slug": slug, "reason": "already_sent"})
            continue

        # Günlük limite ulaşıldı mı?
        if sent_today + sent_count >= DAILY_LIMIT:
            print(f"\n  Günlük limit doldu. Kalan {len(leads) - i + 1} lead yarına bırakıldı.")
            break

        # Mesajı hazırla
        try:
            to  = normalize_phone(lead["phone"])
            msg = build_message(lead)
        except (ValueError, KeyError) as e:
            print(f"  [{i:02d}] HATA  | {lead['name']} → {e}")
            log["failed"].append({"slug": slug, "reason": str(e)})
            continue

        # Gönder
        print(f"  [{i:02d}] GÖNDER| {lead['name']}")
        print(f"        {to}")

        if send_real:
            success = send_via_twilio(to, msg)
        else:
            success = simulate_send(to, msg, lead["name"])

        if success:
            sent_count += 1
            log["sent"].append({
                "slug":     slug,
                "name":     lead["name"],
                "phone":    lead["phone"],
                "demo_url": lead["demo_url"],
                "date":     datetime.now().isoformat(),
                "message":  msg,
            })
            print(f"        ✓ Gönderildi")
        else:
            log["failed"].append({"slug": slug, "reason": "send_error"})
            print(f"        ✗ Başarısız")

        save_log(log)  # Her gönderimden sonra kaydet

        # Son leadse bekleme
        if i < len(leads):
            wait = random.uniform(WAIT_MIN, WAIT_MAX)
            print(f"        ⏳ {wait:.0f} saniye bekleniyor...\n")
            time.sleep(wait)

    # Özet
    print(f"\n{'='*60}")
    print(f"  ÖZET")
    print(f"  Gönderilen  : {sent_count}")
    print(f"  Toplam log  : {len(log['sent'])} (tüm zamanlar)")
    print(f"  Başarısız   : {len(log['failed'])}")
    print(f"  Log dosyası : {LOG_FILE}")
    print(f"{'='*60}\n")


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhatsApp Demo Gönderici")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Gerçek gönderim (Twilio API). Yoksa simülasyon çalışır."
    )
    parser.add_argument(
        "--test",
        metavar="TELEFON",
        help="Sadece bu numaraya test mesajı gönder. Örn: --test 05321234567"
    )
    args = parser.parse_args()

    run(send_real=args.send, test_phone=args.test)

"""
demo_generator.py
-----------------
Bir CSV/liste'deki lead verilerini alir,
Jinja2 sablonunu doldurur ve demo HTML dosyalarini uretir.

Kullanim:
  python demo_generator.py
"""
import sys, io
# Windows terminallerde UTF-8 zorunlu
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import urllib.parse
from pathlib import Path
from datetime import datetime

try:
    import jinja2
except ImportError:
    print("Jinja2 yükleniyor...")
    os.system("pip install jinja2")
    import jinja2


# ── AYARLAR ────────────────────────────────────────────────
TEMPLATE_DIR   = Path(__file__).parent / "templates"
OUTPUT_DIR     = Path(__file__).parent / "demos"
BASE_DEMO_URL  = "https://ParsAnalytics.github.io/web-fabrikasi/demos"          # Canlıda: https://demo.senindomain.com
PURCHASE_URL   = "https://satin-al.webfabrika.com.tr"  # Satın alma landing sayfası

# Sektör → şablon dosyası eşleştirmesi
TEMPLATE_MAP = {
    "cekici":       "cekici-yol-yardim.html",
    "yol_yardim":   "cekici-yol-yardim.html",
    "anaokulu":     "anaokulu.html",
    "kres":         "anaokulu.html",
    "kuafor":       "kuafor.html",
    "guzellik":     "kuafor.html",
    "restoran":     "restoran.html",          # yakında
    "tesisat":      "cekici-yol-yardim.html", # geçici
    "elektrik":     "cekici-yol-yardim.html", # geçici
}


# ── ÖRNEK LEAD LİSTESİ ─────────────────────────────────────
# Gerçekte bu liste Apify/Google Places API'den veya CSV'den gelir.
SAMPLE_LEADS = [
    {
        "name": "Karadeniz Yol Yardım",
        "phone": "0532 111 22 33",
        "address": "Kadıköy, İstanbul",
        "city": "Kadıköy",
        "rating": 4.8,
        "review_count": 127,
        "category": "cekici",
        "slug": "karadeniz-yol-yardim-kadikoy",
    },
    {
        "name": "Hızır Oto Kurtarma",
        "phone": "0541 999 00 11",
        "address": "Beşiktaş, İstanbul",
        "city": "Beşiktaş",
        "rating": 4.6,
        "review_count": 83,
        "category": "yol_yardim",
        "slug": "hizir-oto-kurtarma-besiktas",
    },
    {
        "name": "Gökkuşağı Anaokulu",
        "phone": "0212 333 44 55",
        "address": "Üsküdar, İstanbul",
        "city": "Üsküdar",
        "rating": 4.9,
        "review_count": 64,
        "category": "anaokulu",
        "slug": "gokkusagi-anaokulu-uskudar",
    },
    {
        "name": "Minik Adımlar Kreş",
        "phone": "0216 555 66 77",
        "address": "Bağcılar, İstanbul",
        "city": "Bağcılar",
        "rating": 4.7,
        "review_count": 38,
        "category": "kres",
        "slug": "minik-adimlar-kres-bagcilar",
    },
    {
        "name": "Bella Kuaför",
        "phone": "0532 888 99 00",
        "address": "Şişli, İstanbul",
        "city": "Şişli",
        "rating": 4.9,
        "review_count": 142,
        "category": "kuafor",
        "slug": "bella-kuafor-sisli",
    },
    {
        "name": "Güvenli Çekici Hizmetleri",
        "phone": "0505 777 33 44",
        "address": "Üsküdar, İstanbul",
        "city": "Üsküdar",
        "rating": 4.7,
        "review_count": 54,
        "category": "cekici",
        "slug": "guvenli-cekici-uskudar",
    },
]


# ── YARDIMCI FONKSİYONLAR ──────────────────────────────────

def slugify(text: str) -> str:
    """Türkçe metni URL-dostu slug'a dönüştür."""
    replacements = {
        "ı": "i", "ğ": "g", "ü": "u", "ş": "s",
        "ö": "o", "ç": "c", "İ": "i", "Ğ": "g",
        "Ü": "u", "Ş": "s", "Ö": "o", "Ç": "c",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return (
        text.lower()
        .replace(" ", "-")
        .replace("--", "-")
        .strip("-")
    )


def phone_to_wa(phone: str) -> str:
    """'0532 111 22 33' → 'https://wa.me/905321112233'"""
    digits = "".join(filter(str.isdigit, phone))
    if digits.startswith("0"):
        digits = "90" + digits[1:]
    return f"https://wa.me/{digits}"


def get_template(category: str) -> str:
    """Sektöre göre şablon dosya adını döndür."""
    return TEMPLATE_MAP.get(category, "cekici-yol-yardim.html")


def generate_demo(lead: dict) -> dict:
    """
    Tek bir lead için demo HTML üretir.
    Döndürür: {'slug': ..., 'url': ..., 'output_path': ...}
    """
    slug = lead.get("slug") or slugify(f"{lead['name']}-{lead['city']}")
    template_file = get_template(lead["category"])
    template_path = TEMPLATE_DIR / template_file

    if not template_path.exists():
        print(f"  ⚠️  Şablon bulunamadı: {template_path} — atlanıyor.")
        return {}

    # Jinja2 ortamı
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    # Jinja2'ye urlencode filtresi ekle
    env.filters["urlencode"] = urllib.parse.quote_plus

    template = env.get_template(template_file)

    # Şablona gönderilecek değişkenler
    context = {
        "business_name": lead["name"],
        "phone":         lead["phone"],
        "address":       lead["address"],
        "city":          lead["city"],
        "rating":        lead.get("rating", 4.5),
        "review_count":  lead.get("review_count", 30),
        "whatsapp_link": phone_to_wa(lead["phone"]),
        "demo_cta_url":  f"{PURCHASE_URL}/?lead={slug}",
        "generated_at":  datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    html = template.render(**context)

    # Çıktı dizini oluştur
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

    demo_url = f"{BASE_DEMO_URL}/{slug}/"
    print(f"  ✅ {lead['name']:35s} → {demo_url}")

    return {
        "slug":        slug,
        "name":        lead["name"],
        "phone":       lead["phone"],
        "demo_url":    demo_url,
        "output_path": str(out_file),
    }


# ── ANA ÇALIŞMA ────────────────────────────────────────────

def run(leads: list = None) -> list:
    """
    Tüm leadler için demo üretir.
    leads parametresi verilmezse SAMPLE_LEADS kullanılır.
    """
    if leads is None:
        leads = SAMPLE_LEADS

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n🏭 Demo üretimi başlıyor — {len(leads)} lead\n")
    results = []

    for lead in leads:
        result = generate_demo(lead)
        if result:
            results.append(result)

    # Sonuçları JSON'a kaydet (WhatsApp gönderim scriptinde kullanmak için)
    report_path = OUTPUT_DIR / "generated_demos.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Rapor kaydedildi: {report_path}")
    print(f"✨ Toplam üretilen: {len(results)}/{len(leads)} demo\n")

    return results


# ── DEMO SUNUCU (test için) ─────────────────────────────────

def serve_demos():
    """
    Üretilen demoları localhost:8000'de sunar.
    Sadece test amaçlıdır.
    """
    import http.server
    import socketserver
    import threading

    os.chdir(OUTPUT_DIR.parent)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("🌐 Demo sunucu: http://localhost:8000/demos/")
        print("   (Durdurmak için Ctrl+C)\n")
        httpd.serve_forever()


if __name__ == "__main__":
    import sys

    results = run()

    if "--serve" in sys.argv:
        serve_demos()
    else:
        print("💡 İpucu: Demo sayfaları tarayıcıda açmak için şunu çalıştır:")
        print("   python demo_generator.py --serve\n")
        if results:
            print("Üretilen demo linkleri:")
            for r in results:
                print(f"  • {r['name']:35s} → {r['demo_url']}")

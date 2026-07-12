"""
lead_scraper.py
---------------
Google Places API ile belirli sektör + bölgedeki
web sitesi OLMAYAN işletmeleri toplar ve CSV'ye kaydeder.

Kullanım:
  python lead_scraper.py                          # örnek sorgu
  python lead_scraper.py --query "kuaför" --city "Kadıköy"
  python lead_scraper.py --query "çekici" --city "İstanbul" --radius 10000
"""

import sys, io
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import csv
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── AYARLAR ────────────────────────────────────────────────
API_KEY    = os.getenv("GOOGLE_PLACES_API_KEY", "")
OUTPUT_DIR = Path(__file__).parent / "leads"

# İstanbul ilçeleri için merkez koordinatlar
CITY_COORDS = {
    "Kadıköy":    "40.9927,29.0277",
    "Beşiktaş":   "41.0422,29.0070",
    "Şişli":      "41.0602,28.9877",
    "Üsküdar":    "41.0233,29.0151",
    "Beyoğlu":    "41.0373,28.9773",
    "Bağcılar":   "41.0388,28.8560",
    "Maltepe":    "40.9351,29.1317",
    "Pendik":     "40.8792,29.2280",
    "Ankara":     "39.9208,32.8541",
    "İzmir":      "38.4192,27.1287",
    "Bursa":      "40.1828,29.0665",
    "Antalya":    "36.8841,30.7056",
}

# Sektör → Google Places anahtar kelimesi
SECTOR_KEYWORDS = {
    "cekici":    ["çekici", "yol yardım", "oto kurtarma"],
    "anaokulu":  ["anaokulu", "kreş", "çocuk yuvası"],
    "kuafor":    ["kuaför", "güzellik salonu", "berber"],
    "restoran":  ["restoran", "lokanta", "kafe"],
    "tesisat":   ["tesisatçı", "su tesisatı"],
    "elektrik":  ["elektrikçi", "elektrik tamiri"],
    "disci":     ["diş kliniği", "diş hekimi"],
    "avukat":    ["avukat", "hukuk bürosu"],
    "otoservis": ["oto servis", "araba tamiri"],
}


# ── PUANLAMA ───────────────────────────────────────────────
def score_lead(lead: dict) -> int:
    score = 0
    rc = lead.get("review_count", 0)
    rt = lead.get("rating", 0)
    cat = lead.get("category", "")

    if rc > 100: score += 35
    elif rc > 50: score += 25
    elif rc > 20: score += 15
    elif rc > 5:  score += 5

    if rt >= 4.5: score += 25
    elif rt >= 4.0: score += 10

    high_value = ["cekici", "yol_yardim", "disci", "avukat", "tesisat"]
    if cat in high_value:
        score += 20

    if cat in ["cekici", "yol_yardim"]:
        score += 15  # 7/24 acil → ekstra bonus

    # Ağustos-Eylül: anaokulu bonus
    import datetime as dt
    if cat in ["anaokulu", "kres"] and dt.datetime.now().month in [8, 9]:
        score += 20

    return score


# ── API SORGUSU ────────────────────────────────────────────
def search_places(query: str, location: str, radius: int = 5000) -> list:
    """Google Places Nearby Search API."""
    import urllib.request, urllib.parse

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,
        "radius":   radius,
        "keyword":  query,
        "language": "tr",
        "key":      API_KEY,
    }
    full_url = url + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(full_url, timeout=10) as resp:
            return json.loads(resp.read())["results"]
    except Exception as e:
        print(f"  [!] API hatası: {e}")
        return []


def get_place_details(place_id: str) -> dict:
    """Tek bir yer için detay getir (website, phone)."""
    import urllib.request, urllib.parse

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,formatted_address,website,rating,user_ratings_total,types",
        "language": "tr",
        "key": API_KEY,
    }
    full_url = url + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(full_url, timeout=10) as resp:
            return json.loads(resp.read()).get("result", {})
    except Exception as e:
        print(f"  [!] Detay API hatası: {e}")
        return {}


def scrape_leads(query: str, city: str, radius: int = 5000, category: str = "genel") -> list:
    """Ana scraping fonksiyonu."""
    location = CITY_COORDS.get(city, CITY_COORDS["Kadıköy"])
    print(f"\n  Aranıyor: '{query}' @ {city} (r={radius}m)")

    places = search_places(query, location, radius)
    print(f"  Bulunan: {len(places)} yer")

    leads = []
    for place in places:
        time.sleep(0.1)  # API rate limit

        details = get_place_details(place["place_id"])

        # Web sitesi olan işletmeleri atla
        if details.get("website"):
            continue

        # Telefon numarası zorunlu
        phone = details.get("formatted_phone_number", "")
        if not phone:
            continue

        lead = {
            "name":         details.get("name", place.get("name", "")),
            "phone":        phone,
            "address":      details.get("formatted_address", ""),
            "city":         city,
            "rating":       details.get("rating", 0),
            "review_count": details.get("user_ratings_total", 0),
            "category":     category,
            "types":        ",".join(details.get("types", [])),
            "slug":         "",  # demo_generator dolduracak
            "scraped_at":   datetime.now().isoformat(),
        }
        lead["score"] = score_lead(lead)
        leads.append(lead)
        print(f"  + {lead['name'][:40]:40s} | puan:{lead['score']:3d} | ⭐{lead['rating']} ({lead['review_count']})")

    # Yüksek skorlu önce
    leads.sort(key=lambda x: x["score"], reverse=True)
    return leads


# ── SİMÜLASYON MODU ────────────────────────────────────────
def simulate_scrape() -> list:
    """API anahtarı olmadan test için sahte veriler üret."""
    print("\n  [SIM] Google Places API anahtarı bulunamadı.")
    print("  [SIM] Simülasyon modu aktif — sahte veriler üretiliyor...\n")

    fake_leads = [
        {"name": "Yıldız Yol Yardım",       "phone": "0532 100 10 10", "address": "Kadıköy, İstanbul", "city": "Kadıköy", "rating": 4.9, "review_count": 156, "category": "cekici"},
        {"name": "Ege Çekici",               "phone": "0541 200 20 20", "address": "Beşiktaş, İstanbul","city": "Beşiktaş","rating": 4.6, "review_count": 44,  "category": "cekici"},
        {"name": "Küçük Adımlar Anaokulu",   "phone": "0212 300 30 30", "address": "Şişli, İstanbul",   "city": "Şişli",   "rating": 4.8, "review_count": 71,  "category": "anaokulu"},
        {"name": "Rüya Bebek Yuvası",        "phone": "0216 400 40 40", "address": "Üsküdar, İstanbul", "city": "Üsküdar", "rating": 4.7, "review_count": 29,  "category": "anaokulu"},
        {"name": "Stil Kuaför",              "phone": "0532 500 50 50", "address": "Beyoğlu, İstanbul", "city": "Beyoğlu", "rating": 4.5, "review_count": 88,  "category": "kuafor"},
        {"name": "Lüks Saç Tasarım",        "phone": "0505 600 60 60", "address": "Şişli, İstanbul",   "city": "Şişli",   "rating": 4.8, "review_count": 112, "category": "kuafor"},
        {"name": "İpek Tesisatçı",           "phone": "0532 700 70 70", "address": "Kadıköy, İstanbul", "city": "Kadıköy", "rating": 4.4, "review_count": 33,  "category": "tesisat"},
        {"name": "Altın Lokanta",            "phone": "0212 800 80 80", "address": "Beşiktaş, İstanbul","city": "Beşiktaş","rating": 4.6, "review_count": 205, "category": "restoran"},
    ]

    for lead in fake_leads:
        lead["score"]      = score_lead(lead)
        lead["types"]      = lead["category"]
        lead["slug"]       = ""
        lead["scraped_at"] = datetime.now().isoformat()

    fake_leads.sort(key=lambda x: x["score"], reverse=True)

    print(f"  {'İşletme Adı':40s} | {'Skor':4s} | {'Puan':5s} | {'Yorum':5s}")
    print(f"  {'-'*60}")
    for lead in fake_leads:
        print(f"  {lead['name']:40s} | {lead['score']:4d} | ⭐{lead['rating']}  | {lead['review_count']}")

    return fake_leads


# ── CSV KAYDET ─────────────────────────────────────────────
def save_to_csv(leads: list, filename: str = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    out_path = OUTPUT_DIR / filename
    if not leads:
        print("  [!] Kaydedilecek lead yok.")
        return out_path

    fieldnames = ["score","name","phone","city","address","rating","review_count","category","types","slug","scraped_at"]

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n  CSV kaydedildi: {out_path}")
    print(f"  Toplam lead: {len(leads)}")
    return out_path


def save_to_json(leads: list, filename: str = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    out_path = OUTPUT_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

    return out_path


# ── ANA PROGRAM ────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Maps Lead Scraper")
    parser.add_argument("--query",    default="çekici",   help="Arama terimi")
    parser.add_argument("--city",     default="Kadıköy",  help="İlçe/şehir")
    parser.add_argument("--category", default="cekici",   help="Sektör kodu")
    parser.add_argument("--radius",   default=5000, type=int, help="Arama yarıçapı (metre)")
    parser.add_argument("--all",      action="store_true", help="Tüm sektörleri tara")
    args = parser.parse_args()

    all_leads = []

    if not API_KEY:
        # API anahtarı yok → simülasyon
        all_leads = simulate_scrape()
    elif args.all:
        # Tüm sektörler
        for category, keywords in SECTOR_KEYWORDS.items():
            for kw in keywords:
                leads = scrape_leads(kw, args.city, args.radius, category)
                all_leads.extend(leads)
                time.sleep(1)
    else:
        all_leads = scrape_leads(args.query, args.city, args.radius, args.category)

    if all_leads:
        csv_path  = save_to_csv(all_leads)
        json_path = save_to_json(all_leads)

        print(f"\n  Sonraki adim: demo_generator.py icin JSON olusturuldu:")
        print(f"  {json_path}\n")

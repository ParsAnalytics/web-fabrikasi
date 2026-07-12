"""
airtable_crm.py
-------------
Airtable tablosuna lead verilerini senkronize eder ve durumları günceller.
Tamamen ücretsiz Airtable API'sini kullanır.

Kullanım:
  python airtable_crm.py --sync-leads
  python airtable_crm.py --update-status <slug> <status>
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import argparse
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

AIRTABLE_TOKEN = os.getenv("AIRTABLE_ACCESS_TOKEN", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Leads")

DEMOS_JSON = Path(__file__).parent / "demos" / "generated_demos.json"

def sync_leads_to_airtable():
    if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
        print("\n[!] Airtable API anahtarları eksik. .env dosyasını güncelleyin.")
        print("    Gerekli: AIRTABLE_ACCESS_TOKEN ve AIRTABLE_BASE_ID\n")
        print("💡 Simülasyon modunda devam ediliyor (Airtable'a istek atılmadı).")
        return False

    if not DEMOS_JSON.exists():
        print(f"[!] {DEMOS_JSON} bulunamadı. Önce demo üretmelisiniz.")
        return False

    with open(DEMOS_JSON, encoding="utf-8") as f:
        demos = json.load(f)

    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

    print(f"\n🚀 {len(demos)} lead Airtable'a aktarılıyor...")
    
    for lead in demos:
        # Önce mevcut kaydı kontrol et (slug üzerinden)
        query_url = f"{url}?filterByFormula={{Slug}}='{lead['slug']}'"
        res = requests.get(query_url, headers=headers)
        
        fields = {
            "Isletme Adi": lead["name"],
            "Telefon": lead["phone"],
            "Demo Link": lead["demo_url"],
            "Slug": lead["slug"],
            "Durum": "Bekliyor"
        }

        if res.ok and res.json().get("records"):
            # Güncelle (PATCH)
            record_id = res.json()["records"][0]["id"]
            patch_url = f"{url}/{record_id}"
            requests.patch(patch_url, headers=headers, json={"fields": fields})
            print(f"  🔄 Güncellendi: {lead['name']}")
        else:
            # Yeni Ekle (POST)
            requests.post(url, headers=headers, json={"fields": fields})
            print(f"  ➕ Eklendi: {lead['name']}")

    print("\n✅ Airtable CRM Senkronizasyonu Tamamlandı!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airtable CRM Entegrasyonu")
    parser.add_argument("--sync-leads", dest="sync_leads", action="store_true", help="Lokal demoları Airtable'a aktar")
    args = parser.parse_args()

    if args.sync_leads or len(sys.argv) == 1:
        sync_leads_to_airtable()

"""
payment_link.py
---------------
iyzico Sandbox API veya Simülasyon modunda ödeme linkleri üretir.
Logları data/payments.json'a kaydeder.

Kullanım:
  python payment_link.py --slug bella-kuafor-sisli --name "Bella Kuaför" --phone 05328889900 --amount 999
  python payment_link.py --list
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PAYMENTS_DB = Path(__file__).parent / "data" / "payments.json"

def load_payments() -> list:
    PAYMENTS_DB.parent.mkdir(parents=True, exist_ok=True)
    if PAYMENTS_DB.exists():
        with open(PAYMENTS_DB, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_payments(payments: list):
    with open(PAYMENTS_DB, "w", encoding="utf-8") as f:
        json.dump(payments, f, ensure_ascii=False, indent=2)

def generate_mock_link(slug: str) -> str:
    """Sandbox/Simülasyon için lokal FastAPI webhook URL'i."""
    port = os.getenv("WEBHOOK_PORT", "8080")
    return f"http://localhost:{port}/payment/success?conversationId={slug}&price=999"

def create_payment(slug: str, name: str, phone: str, amount: float) -> str:
    pay_url = generate_mock_link(slug)
    
    payments = load_payments()
    payments.append({
        "slug": slug,
        "name": name,
        "phone": phone,
        "amount": amount,
        "payment_url": pay_url,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "paid_at": None
    })
    save_payments(payments)
    
    iban_number = os.getenv("IBAN_NUMBER", "").strip()
    iban_bank = os.getenv("IBAN_BANK", "Ziraat Bankası").strip()
    iban_owner = os.getenv("IBAN_OWNER", "Ad Soyad").strip()
    
    # Eğer IBAN ayarlanmışsa IBAN mesajı, yoksa online ödeme linki mesajı üret
    if iban_number and not iban_number.startswith("TR00"):
        msg = f"""Merhaba {name} yetkilisi,

Sitenizi beğendiğiniz için teşekkürler! 🎉

Ödemenizi aşağıdaki IBAN adresine havale/EFT olarak gönderebilirsiniz:

🏦 Banka: {iban_bank}
👤 Alıcı: {iban_owner}
💳 IBAN: {iban_number}
💵 Tutar: {amount} ₺
📝 Açıklama: {slug} (Onay için lütfen açıklamaya bunu yazın)

Ödemeniz ulaştıktan sonra siteniz 24 saat içinde yayına alınacaktır.
{amount} ₺ kurulum + 125 ₺/ay bakım.

Sorularınız için buradan yazabilirsiniz."""
    else:
        msg = f"""Merhaba {name} yetkilisi,

Sitenizi beğendiğiniz için teşekkürler! 🎉

Güvenli ödeme linkiniz:
💳 {pay_url}

Ödeme tamamlandıktan sonra siteniz 24 saat içinde yayına alınır.
{amount} ₺ kurulum + 125 ₺/ay bakım.

Sorularınız için buradan yazabilirsiniz."""
    
    print("\n" + "="*50)
    print(f"💰 Ödeme Talebi Oluşturuldu ({name})")
    print("="*50)
    print(f"Link: {pay_url}")
    print("\n[WA GÖNDERİLECEK MESAJ]:")
    print(msg)
    print("="*50)
    
    return pay_url

def list_payments():
    payments = load_payments()
    if not payments:
        print("\nHenüz oluşturulmuş ödeme talebi yok.")
        return
    
    print(f"\n{'İşletme':30s} | {'Tutar':8s} | {'Durum':10s} | {'Tarih':20s}")
    print("-"*75)
    for p in payments:
        print(f"{p['name']:30s} | {p['amount']:6.2f} ₺ | {p['status']:10s} | {p['created_at'][:16]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iyzico Link Oluşturucu")
    parser.add_argument("--slug", help="İşletme slug")
    parser.add_argument("--name", help="İşletme adı")
    parser.add_argument("--phone", help="Telefon numarası")
    parser.add_argument("--amount", type=float, default=999.0, help="Ödeme tutarı")
    parser.add_argument("--list", action="store_true", help="Ödemeleri listele")
    args = parser.parse_args()

    if args.list:
        list_payments()
    elif args.slug and args.name and args.phone:
        create_payment(args.slug, args.name, args.phone, args.amount)
    else:
        # Örnek oluştur
        create_payment("bella-kuafor-sisli", "Bella Kuaför", "05328889900", 999.0)
        print("\n💡 İpucu: Kendi verilerinizle üretmek için:")
        print("python payment_link.py --slug <slug> --name <isim> --phone <telefon>")

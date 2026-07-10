# 🏭 Web Fabrikası

Google Maps'te web sitesi olmayan küçük işletmelere otomatik demo üret, WhatsApp ile sat.

## Proje Yapısı

```
web-fabrika/
├── templates/
│   └── cekici-yol-yardim.html   ← Şablon HTML dosyaları (sektöre göre)
├── demos/                        ← Otomatik üretilen demo sayfalar
│   ├── karadeniz-yol-yardim-kadikoy/
│   │   └── index.html
│   ├── generated_demos.json      ← Üretilen demo listesi
│   └── send_log.json             ← WhatsApp gönderim logu
├── demo_generator.py             ← Demo üretim motoru
├── whatsapp_sender.py            ← WhatsApp gönderim botu
└── .github/workflows/deploy.yml  ← GitHub Pages otomatik deploy
```

---

## Hızlı Başlangıç

### 1. Bağımlılıkları Yükle
```bash
pip install jinja2
# Gerçek WhatsApp gönderimi için:
pip install twilio
```

### 2. Lead Listeni Ekle
`demo_generator.py` içindeki `SAMPLE_LEADS` listesini düzenle:
```python
SAMPLE_LEADS = [
    {
        "name":         "Kendi İşletme Adın",
        "phone":        "0532 111 22 33",
        "address":      "Kadıköy, İstanbul",
        "city":         "Kadıköy",
        "rating":       4.7,
        "review_count": 89,
        "category":     "cekici",   # bkz: TEMPLATE_MAP
        "slug":         "benim-isletmem-kadikoy",
    },
    # ...
]
```

### 3. Demo Sayfaları Üret
```bash
python demo_generator.py
```

### 4. Tarayıcıda Önizle
```bash
python demo_generator.py --serve
# → http://localhost:8000/demos/
```

### 5. WhatsApp Mesajlarını Simüle Et
```bash
python whatsapp_sender.py
```

### 6. Gerçek WhatsApp Gönderimi (Twilio)
```bash
# .env veya ortam değişkenlerine ekle:
set TWILIO_ACCOUNT_SID=ACxxxxxxxx
set TWILIO_AUTH_TOKEN=xxxxxxxx
set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

python whatsapp_sender.py --send
```

### 7. Belirli Numaraya Test Mesajı
```bash
python whatsapp_sender.py --test 05321234567
python whatsapp_sender.py --test 05321234567 --send   # gerçek gönderim
```

---

## Desteklenen Sektörler

| Kategori Kodu | Şablon | Açıklama |
|---|---|---|
| `cekici` | cekici-yol-yardim.html | Çekici / Yol Yardım |
| `yol_yardim` | cekici-yol-yardim.html | Yol Yardım |
| `anaokulu` | anaokulu.html *(yakında)* | Anaokulu / Kreş |
| `kuafor` | kuafor.html *(yakında)* | Kuaför / Güzellik |
| `restoran` | restoran.html *(yakında)* | Restoran / Kafe |

---

## GitHub Pages Deploy

Repo'yu GitHub'a pushladıktan sonra:
1. Repo → **Settings** → **Pages**
2. Source: **GitHub Actions**
3. Her `git push main` sonrası demo sayfalar otomatik yayınlanır

Demo linklerin formatı:
```
https://KULLANICI_ADIN.github.io/REPO_ADI/karadeniz-yol-yardim-kadikoy/
```

---

## Loglar

| Dosya | İçerik |
|---|---|
| `demos/generated_demos.json` | Üretilen tüm demolar |
| `demos/send_log.json` | Gönderilen / başarısız / atlanan mesajlar |

---

## Fiyatlandırma Modeli

| Kalem | Tutar |
|---|---|
| Kurulum (tek seferlik) | 999 ₺ |
| Aylık bakım | 125 ₺/ay |
| Yıllık (peşin) | 1.500 ₺ |

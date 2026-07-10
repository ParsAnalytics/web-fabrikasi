# 🏭 Web Fabrikası — Yapılan Geliştirmeler & Canlıya Geçiş Özeti

Bu belgede, Google Maps üzerinde web sitesi olmayan küçük işletmeleri tespit edip otomatik demo üreten ve WhatsApp ile satan otomasyon sistemimizin geliştirme aşamaları ve doğrulama sonuçları yer almaktadır.

---

## 🛠️ Neler Geliştirildi?

1. **Çoklu Sektör Şablonları (`templates/`)**:
   - 🚨 **Yol Yardım / Çekici** (`cekici-yol-yardim.html`): Sarı/Siyah acil durum konseptli, anında arama odaklı.
   - 🎒 **Anaokulu / Kreş** (`anaokulu.html`): Sarı/Mor, neşeli, ön kayıt odaklı.
   - ✂️ **Kuaför / Güzellik Salonu** (`kuafor.html`): Koyu lüks gold detaylı, randevu odaklı.
   - 🍽️ **Restoran / Kafe** (`restoran.html`): Koyu/Sıcak tonlar, menü ve rezervasyon odaklı.

2. **Otomasyon Motorları (`.py`)**:
   - `lead_scraper.py`: Google Places API ile web sitesi olmayan işletmeleri filtreleyerek toplar ve yorum sayıları/puanlarına göre lead skorlaması yapar.
   - `demo_generator.py`: Jinja2 kullanarak lead verilerini sektörel şablonlara yerleştirir ve 30 saniyede hazır statik web sayfaları üretir.
   - `whatsapp_sender.py`: A/B test mesajları hazırlar, spam engeli için rastgele bekleme süreleri (35-90 sn) uygular ve Twilio API entegrasyonu sunar.
   - `payment_link.py`: iyzico entegrasyonu ile müşteriye özel ödeme linki ve WhatsApp sipariş mesajı oluşturur.
   - `webhook_server.py`: FastAPI ile ödeme bildirimlerini alır, ödeme yapan işletmenin demosundaki "Satın Al" banner'ını kaldırıp siteyi anında aktifleştirir.

3. **Yönetim Paneli (`dashboard.html`)**:
   - HTML/JS ile yerel veritabanı (JSON) dosyalarını okuyan, toplam ciroyu, aktif müşterileri ve son olayları (tıklama, ödeme) canlı gösteren dashboard paneli.

4. **Yayın ve Bulut Kurulumu (`github_setup.py`)**:
   - Projenin tek tuşla **[ParsAnalytics/web-fabrikasi](https://github.com/ParsAnalytics/web-fabrikasi)** GitHub reposuna pushlanması ve **GitHub Pages** (Actions workflow) ile canlı demo linklerinin yayınlanması sağlandı.

---

## 🧪 Doğrulama ve Test Sonuçları

- **Demo Üretim Testi**: 7 örnek lead için şablonlar başarıyla derlendi ve `demos/` klasörüne aktarıldı.
- **WhatsApp Gönderim Testi**: Simülasyon modunda 35-90 saniye aralıklarla bekleme süreleri ve kişiselleştirilmiş A/B test mesajlarının başarıyla üretildiği doğrulandı.
- **FastAPI & Ödeme Webhook Testi**: Simüle edilmiş iyzico ödeme linki oluşturulup tıklandığında webhook sunucusunun bunu başarıyla yakaladığı, veritabanına kaydettiği ve demoyu canlı sürüme (banner olmadan) dönüştürdüğü doğrulandı.
- **Yönetim Paneli Testi**: Dashboard'un 5 saniyede bir verileri güncellediği ve aktif müşterileri anlık yansıttığı test edildi.

---

## 📈 Canlıya Geçiş İçin Son Yapılması Gerekenler
1. `github_setup.py` başarıyla çalıştı ve GitHub Pages canlıda. İlerleyen dönemlerde yeni lead eklediğinizde sadece `python demo_generator.py` çalıştırıp kodları git'e pushlamanız yeterli olacaktır (GitHub Pages otomatik güncellenir).
2. Gerçek WhatsApp gönderimleri için `.env` dosyasındaki Twilio bilgilerini güncelleyin.
3. Gerçek lead kazıma için `.env` dosyasındaki `GOOGLE_PLACES_API_KEY` alanını doldurun.

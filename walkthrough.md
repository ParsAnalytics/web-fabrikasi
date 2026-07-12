# 🏭 Web Fabrikası — AI & Playwright Entegrasyon walkthrough

Bu belgede, Google Haritalar üzerinde web sitesi olmayan küçük işletmeler için tamamen kişiselleştirilmiş web siteleri ve demo videoları üreten otomasyon sistemimizin en son sürüm geliştirmeleri ve doğrulama sonuçları yer almaktadır.

---

## 🛠️ Neler Geliştirildi?

1. **Claude (Anthropic) AI Entegrasyonu (`ai_optimizer.py`)**:
   - Google Maps'ten kazınan lead'ler için Claude API yardımıyla otomatik **Teşhis (Diagnostics)**, **Site Brifi** ve **Kişiselleştirilmiş Soğuk Satış Mesajı** üretir.
   - API anahtarı girilmediğinde sistemin çökmesini engellemek için **Simülasyon/Fallback** modu barındırır.

2. **Dinamik HTML Şablonları & Demo Motoru (`demo_generator.py`)**:
   - Jinja2 şablonları (`cekici-yol-yardim.html`, `anaokulu.html` vb.) AI tarafından üretilen özel H1 başlığı, alt başlığı, 3 ana hizmet başlık/açıklamaları ve hakkımızda metinlerini dinamik olarak derler.
   - En son taranan `leads_*.json` dosyasını otomatik olarak bularak o listedeki lead'lere özel demo üretir.

3. **Playwright Mobil Demo Videosu Motoru (`video_generator.py`)**:
   - Playwright'ın Chromium altyapısını kullanarak üretilen demoyu mobil cihaz dikey (9:16) formatında açar.
   - Sayfada yavaşça aşağı kaydırma (cinematic scroll) yaparak 10 saniyelik demo videosunu (`demo.webm`) tamamen yerel ve otomatik olarak kaydeder.

4. **Premium Koyu Arayüz (`dashboard.html` & `server.py`)**:
   - Plus Jakarta Sans fontları ve Indigo/Gold odaklı cam efektli (glassmorphism) modern bir koyu tema tasarlandı.
   - Arayüze "AI ile Optimize Et", "Video Üret" ve modal içinde "Videoyu Oynat" özellikleri eklendi.
   - Sunucunun tek başına demoları ve videoları servis etmesi için FastAPI `StaticFiles` yönlendirmesi eklendi.

---

## 🧪 Doğrulama ve Test Sonuçları

- **AI Optimizer Fallback Testi**: API key yokluğunda Türkçe ve emojili teşhis ve tekliflerin başarıyla üretildiği doğrulandı.
- **Dinamik Demo Üretimi**: Taranan 8 lead için özelleştirilmiş HTML sayfaları 1 saniyede başarıyla derlendi.
- **Playwright Video Kaydı**: 9:16 dikey mobil video üretimi test edildi ve `demos/yildiz-yol-yardim-kadikoy/demo.webm` olarak başarıyla kaydedildi.
- **FastAPI backend**: `/api/run/optimizer` ve `/api/run/video` endpoint'leri başarıyla test edildi.

---

## 🚀 Sistemi Başlatma ve Çalıştırma

1. **API Ayarları**:
   - Claude'un en iyi performansla çalışması için `.env` dosyanıza `ANTHROPIC_API_KEY=your_key` ekleyin.
   
2. **Sunucuyu Çalıştırın**:
   ```bash
   python server.py
   ```
   
3. **Kontrol Paneline Giriş Yapın**:
   - Tarayıcınızda `http://localhost:8000` adresini açın.
   - Varsayılan şifre olan `admin123` ile giriş yapın.
   - Artık lead'lerinizi görebilir, AI optimizasyonlarını tetikleyebilir ve Playwright ile dikey mobil videolarını üreterek satış havuzunuzu yönetebilirsiniz!

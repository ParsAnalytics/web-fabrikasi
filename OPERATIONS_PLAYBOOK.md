# 🚀 Web Fabrikası — Operasyon ve Satış Kapatma Rehberi

Bu rehber, teknik otomasyonu tamamlanmış olan sistemimizin sahada (WhatsApp / Telefon üzerinden) en yüksek dönüşüm oranıyla çalışmasını sağlamak için hazırlanmıştır.

---

## 1. İlk WhatsApp İletişim Stratejisi

Küçük işletme sahipleri yoğundur. Uzun, teknik ve sıkıcı mesajları okumazlar. İletişim **kısa, görsel ve doğrudan fayda odaklı** olmalıdır.

### 📱 Altın Mesaj Şablonu
> "Merhaba [İşletme Adı] yetkilisi 👋
> 
> Google Haritalar'da sitenizin olmadığını fark ettim ve müşterilerinizin size doğrudan ulaşabilmesi için 10 dakikada özel bir mobil web sitesi taslağı hazırladım:
> 
> 🔗 **[Canlı Demo Linki]**
> 
> Eğer tasarımı beğenirseniz; kendi alan adınız (.com.tr) ve WhatsApp butonunuzla birlikte 24 saat içinde yayına alabiliriz. Kurulum ücreti tek seferlik 999 TL'dir.
> 
> İnceleyip dönüş yaparsanız sevinirim. İyi çalışmalar!"

### ⚠️ Dikkat Edilmesi Gerekenler
* **Spam Engeli:** Günlük kişisel hat limitiniz maksimum 50 mesaj olmalıdır. Twilio veya resmi API kullanmıyorsanız mesajları 1-2 dakika arayla (otomatik scriptimizin yaptığı gibi) gönderin.
* **Kişiselleştirme:** Mesajın başına mutlaka işletmenin Maps'teki adını ekleyin. "Merhaba Çekici Ahmet Usta" gibi samimi hitaplar dönüşü %40 artırır.

---

## 2. En Sık Gelen 5 İtiraz ve Karşılama Metinleri

### İtiraz 1: "Bizim zaten Instagram / Facebook sayfamız var, siteye gerek yok."
* **Cevap:** *"Çok haklısınız, sosyal medya harika bir vitrin. Ancak acil bir durumda (örn: yolda kalan bir sürücü veya acil tesisat ihtiyacı olan biri) insanlar Instagram'da arama yapmazlar. Doğrudan Google'a girip ararlar. Siteniz olmadığında bu müşteriler doğrudan rakiplerinize gidiyor."*

### İtiraz 2: "999 TL dışında başka bir ücret var mı? Yıllık ne ödeyeceğiz?"
* **Cevap:** *"Gizli veya sürpriz bir ücret yok. İlk yıl alan adınız, SSL güvenlik sertifikanız ve hostinginiz 999 TL'lik kurulum ücretine dahildir. İkinci yıldan itibaren sitenizin açık kalması ve teknik destek için aylık sadece 125 TL (yıllık 1500 TL) güncelleme bedeli mevcuttur."*

### İtiraz 3: "Sitede şu yazıyı / logoyu değiştirebilir miyiz?"
* **Cevap:** *"Elbette. Kurulum öncesi logonuzu, çalışma saatlerinizi ve hizmet verdiğiniz bölgeleri tamamen sizin bilgilerinize göre güncelliyoruz. Yılda 2 kez de ücretsiz içerik güncelleme hakkınız bulunuyor."*

### İtiraz 4: "Güvenebilir miyiz? Ödemeyi yaptıktan sonra sitenin açılacağı ne malum?"
* **Cevap:** *"Ödemenizi Türkiye'nin en güvenli ödeme altyapısı olan iyzico (veya PayTR) güvencesiyle, faturalı ve korumalı link üzerinden yapıyorsunuz. Zaten sitenizin tasarımı şu an hazır, ödemeden hemen sonra 24 saat içinde kendi alan adınızla yayına alıyoruz."*

---

## 3. Günlük Operasyonel Rutin (Zaman/Maliyet Yönetimi)

Bu iş modelinin batmaması için **revizyon taleplerine harcanan zamanın sıfıra yakın olması** gerekir.

1. **Adım:** Sabah `python lead_scraper.py` çalıştırıp 100 lead topla.
2. **Adım:** `python demo_generator.py` ile demoları topluca üret ve GitHub Pages'e yükle.
3. **Adım:** `python whatsapp_sender.py` ile saatte 10-15 mesaj gidecek şekilde botu başlat.
4. **Adım:** Gelen cevapları `dashboard.html` üzerinden izle. İlgilenenlere `payment_link.py` ile ödeme linki gönder.
5. **Adım:** Ödeme geldiğinde `webhook_server.py` otomatik olarak banner'ı kaldırıp siteyi aktifleştirsin. Müşteriye bilgileri teslim et. **Müşteriyle telefon görüşmesini maksimum 3 dakika ile sınırlandır.**

---

## 4. İlerleyen Aşamalarda Ölçekleme (Upsell)

İlk 50 aboneye ulaştıktan sonra gelirini ikiye katlamak için aynı müşterilere şu ek hizmetleri satabilirsin:
* **Google Harita Optimizasyonu (GBP):** Aylık 250 TL karşılığında harita yorumlarını yanıtlama ve haftalık fotoğraf yükleme. (Yarı-otomasyon araçlarıyla yapılabilir).
* **Profesyonel E-Posta:** `info@isletmeadi.com.tr` kurulumu (Yıllık +300 TL).
* **Ek Sayfa / Blog:** Sabit şablonun dışına çıkan her ek sayfa için tek seferlik +500 TL.

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AIOptimizer:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self.gemini_client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                print("[AI] Anthropic API anahtarı yüklendi, Claude aktif.")
            except ImportError:
                print("[AI] Warning: 'anthropic' paketi bulunamadı.")

        if not self.client and self.gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                print("[AI] Gemini API anahtarı yüklendi, Gemini aktif.")
            except ImportError:
                print("[AI] Warning: 'google-genai' paketi bulunamadı.")

        if not self.client and not self.gemini_client:
            print("[AI] Herhangi bir AI API anahtarı bulunamadı. Simülasyon/Fallback modu aktif.")

    def optimize_lead(self, lead: dict) -> dict:
        """
        Claude veya Gemini API kullanarak tek bir lead için teşhis, site içeriği ve soğuk mesaj üretir.
        Eğer API anahtarı yoksa yerel kurallarla simülasyon çıktısı üretir.
        """
        # Gerekli alanların varlığından emin olalım
        name = lead.get("name", "Bilinmeyen İşletme")
        city = lead.get("city", "İstanbul")
        category = lead.get("category", "genel")
        rating = lead.get("rating", 0)
        review_count = lead.get("review_count", 0)
        address = lead.get("address", "")
        phone = lead.get("phone", "")

        # Eğer API istemcisi yoksa Fallback çalıştır
        if not self.client and not self.gemini_client:
            return self._fallback_optimize(lead)

        prompt = f"""
        Sen kıdemli bir yerel pazarlama stratejistisin. Google Haritalar üzerinde web sitesi olmayan veya çok eski olan yerel bir işletme için web sitesi satışı yapacağız.
        Aşağıdaki işletme detaylarını incele ve bu işletmeye özel 3 ana çıktı üret:

        İşletme Detayları:
        - Adı: {name}
        - Konum (İlçe/Şehir): {city}
        - Sektör: {category}
        - Google Yorum Puanı: {rating}
        - Google Yorum Sayısı: {review_count}
        - Adres: {address}

        İstenen Çıktılar (JSON formatında olmalı ve şu şemaya uymalıdır):
        {{
            "diagnostics": "Mevcut dijital eksiklikler ve ciro kaybını belirten maksimum 50 kelimelik profesyonel analiz.",
            "hero_title": "Web sitesi ana sayfası için dikkat çekici, bu işletmeye özel büyük başlık (H1).",
            "hero_sub": "Başlığın altındaki açıklayıcı alt metin (20 kelime civarı).",
            "about_text": "İşletmenin adını ve konumunu barındıran, müşteriye güven veren samimi bir Hakkımızda yazısı (50-60 kelime).",
            "services": [
                {{"title": "1. Hizmet Başlığı", "desc": "Hizmet açıklaması"}},
                {{"title": "2. Hizmet Başlığı", "desc": "Hizmet açıklaması"}},
                {{"title": "3. Hizmet Başlığı", "desc": "Hizmet açıklaması"}}
            ],
            "cold_message": "İşletmeye WhatsApp/SMS üzerinden gönderilecek samimi, kurumsal olmayan, AI gibi durmayan, işletmenin Maps'teki durumuna (örneğin yüksek yorum sayısı ama sitesinin olmaması vb.) değinen, maketi incelemesi için kibar bir taleple biten 70 kelime altı soğuk satış mesajı."
        }}

        Kurallar:
        - Yanıt sadece geçerli ve temiz bir JSON objesi olmalıdır. Başka hiçbir açıklama, selamlama veya kod bloğu dışı metin ekleme.
        - Tüm metinler Türkçe olmalıdır.
        - AI terminolojisi kullanma.
        """

        # 1. Claude istemcisi varsa onunla devam et
        if self.client:
            try:
                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    temperature=0.7,
                    system="Sen sadece geçerli JSON döndüren yerel bir pazarlama uzmanı yapay zekasın.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                response_text = message.content[0].text.strip()
                return self._parse_and_merge(lead, response_text)
            except Exception as e:
                print(f"[AI] Claude çağrısında hata oluştu: {e}. Gemini veya simülasyona geçiliyor.")

        # 2. Claude yoksa veya hata aldıysa Gemini dene
        if self.gemini_client:
            try:
                from google.genai import types
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                        system_instruction="Sen sadece geçerli JSON döndüren yerel bir pazarlama uzmanı yapay zekasın.",
                    ),
                )
                response_text = response.text.strip()
                return self._parse_and_merge(lead, response_text)
            except Exception as e:
                print(f"[AI] Gemini çağrısında hata oluştu: {e}. Simülasyon moduna geçiliyor.")

        return self._fallback_optimize(lead)

    def _parse_and_merge(self, lead: dict, response_text: str) -> dict:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
            
        optimized_data = json.loads(response_text)
        
        result = lead.copy()
        result.update(optimized_data)
        result["ai_optimized"] = True
        return result

    def _fallback_optimize(self, lead: dict) -> dict:
        """API anahtarı bulunamadığında veya hata oluştuğunda çalışan yerel simülasyon motoru."""
        name = lead.get("name", "Bilinmeyen İşletme")
        city = lead.get("city", "Kadıköy")
        category = lead.get("category", "genel")
        rating = lead.get("rating", 4.5)
        review_count = lead.get("review_count", 25)

        result = lead.copy()
        
        # Sektöre göre hazır şablon metinler
        if category in ["cekici", "yol_yardim"]:
            result["diagnostics"] = f"Google Haritalar'da {review_count} yoruma ve {rating} puana sahip olmanıza rağmen web siteniz yok. {city}'de yolda kalan müşteriler aramalarda rakiplerinizi tercih ediyor ve doğrudan müşteri kaybı yaşıyorsunuz."
            result["hero_title"] = f"{city}'de Güvenilir 7/24 Yol Yardım & Çekici"
            result["hero_sub"] = f"{name} olarak en zor anınızda 20 dakikada yanınızdayız. Güvenli ve hızlı oto çekici."
            result["about_text"] = f"{name}, {city} bölgesinde uzun yıllardır yolda kalan sürücülere güvenli çekici ve acil yol yardım hizmetleri sunmaktadır. Deneyimli ekibimiz ve modern araçlarımızla 7 gün 24 saat kesintisiz hizmet veriyoruz."
            result["services"] = [
                {"title": "Oto Çekici", "desc": "Kaza veya arıza durumunda aracınızı en yakın servise güvenle taşıyoruz."},
                {"title": "Akü Takviye", "desc": "Akü bitmesi durumunda mobil ekiplerimizle yerinde akü takviyesi ve değişimi sağlıyoruz."},
                {"title": "Lastik Yol Yardım", "desc": "Patlayan veya hasar gören lastiklerinizi yerinde hızlıca değiştiriyoruz."}
            ]
            result["cold_message"] = f"Merhaba {name} yetkilisi 👋 Maps'teki {rating} yıldızlı başarınızı gördüm ama siteniz yok. Yolda kalanların size doğrudan ulaşabilmesi için 10 dakikada özel bir mobil site taslağı hazırladım: [demo_url] Beğenirseniz 24 saatte yayına alabiliriz. Kurulum 999 ₺. İncelemek ister misiniz?"
        
        elif category in ["anaokulu", "kres"]:
            result["diagnostics"] = f"Sosyal varlığınız iyi ancak web sitenizin olmaması okul arayan velilerde güven eksikliği yaratıyor. Kayıt dönemlerinde dijital başvuru alamamak okul kontenjanınızın boş kalmasına sebep oluyor."
            result["hero_title"] = f"{city}'nin En Neşeli ve Güvenli Anaokulu"
            result["hero_sub"] = f"{name}'nda MEB onaylı, çocuk dostu eğitim modeli ve uzman pedagog kadrosu."
            result["about_text"] = f"{name}, {city} ilçesinde çocuklarımızın bilişsel, fiziksel ve sosyal gelişimlerini destekleyen modern eğitim alanları sunar. Sevgi dolu ve güvenli bir ortamda geleceğe mutlu adımlar atıyoruz."
            result["services"] = [
                {"title": "MEB Müfredatı", "desc": "Yaş gruplarına uygun, çocuk merkezli modern eğitim ve oyun programları."},
                {"title": "Branş Dersleri", "desc": "İngilizce, robotik kodlama, jimnastik ve müzik gibi zengin içerikler."},
                {"title": "Pedagojik Destek", "desc": "Uzman psikologlar eşliğinde düzenli çocuk gelişimi takibi ve veli bilgilendirme."}
            ]
            result["cold_message"] = f"Merhaba {name} öğretmenim 👋 Google'daki harika veli yorumlarınızı gördüm. Yeni dönemde velilerin sizi daha kolay bulması ve güven duyması için okulunuza özel bir mobil site taslağı hazırladım: [demo_url] Kurulum 999 ₺. İlginizi çekerse detayları konuşabiliriz."

        elif category in ["kuafor", "guzellik"]:
            result["diagnostics"] = f"Güzellik sektöründe görsel kimlik ve online randevu kritik önemdedir. Siteniz olmadığı için arama yapan yeni müşteriler randevu alamıyor ve rakiplerinize yöneliyor."
            result["hero_title"] = f"{city}'de Lüks Saç Tasarım & Güzellik Salonu"
            result["hero_sub"] = f"{name} ile tarzınızı yansıtın. Profesyonel saç, makyaj ve güzellik uygulamaları."
            result["about_text"] = f"{name}, {city} bölgesinde trend saç tasarımları, profesyonel makyaj ve cilt bakımı hizmetleri sunan öncü bir güzellik salonudur. Hijyenik ortamımız ve uzman kadromuzla kendinizi özel hissettiriyoruz."
            result["services"] = [
                {"title": "Saç Tasarım", "desc": "Size özel kesim, boyama, ombre ve keratin bakım uygulamaları."},
                {"title": "Profesyonel Makyaj", "desc": "Gelin makyajı, porselen makyaj ve özel günleriniz için kalıcı dokunuşlar."},
                {"title": "Cilt Bakımı", "desc": "Medikal cilt bakımı, leke tedavisi ve canlandırıcı cilt maskeleri."}
            ]
            result["cold_message"] = f"Merhaba {name} salon sahibi 👋 Google Haritalar'daki güzel puanlarınızı gördüm ama siteniz bulunmuyor. Yeni müşterilerinizin kolayca randevu alabilmesi için size özel şık bir mobil site taslağı hazırladım: [demo_url] Kurulum 999 ₺. Beğenirseniz yayına alabiliriz. Ne dersiniz?"

        elif category in ["restoran", "kafe"]:
            result["diagnostics"] = f"Google Haritalar'da {review_count} yorumunuz var, lezzetleriniz seviliyor. Ancak dijital menünüz ve siteniz olmadığı için eve sipariş vermek isteyen müşteriler sizi bulamıyor."
            result["hero_title"] = f"{city}'de Benzersiz Lezzet & Keyifli Buluşma Noktası"
            result["hero_sub"] = f"{name}'nda taze malzemelerle hazırlanan zengin menü ve şık mekan konsepti."
            result["about_text"] = f"{name}, {city} kalbinde eşsiz dünya mutfağı lezzetlerini ve özel kahve çeşitlerini şık bir atmosferde sunar. Deneyimli şeflerimizin hazırladığı gurme tabaklarla sizleri ağırlamaktan mutluluk duyuyoruz."
            result["services"] = [
                {"title": "Gurme Menü", "desc": "Her damak tadına uygun özenle hazırlanmış burger, pizza ve tatlı çeşitleri."},
                {"title": "Sıcak & Soğuk İçecekler", "desc": "Nitelikli kahve çekirdekleri, taze meyve suları ve özel kokteyller."},
                {"title": "Rezervasyon & Etkinlik", "desc": "Doğum günleri, iş toplantıları veya özel davetleriniz için alan organizasyonu."}
            ]
            result["cold_message"] = f"Merhaba {name} işletmecisi 👋 Yemekleriniz harika yorumlar alıyor ama web siteniz yok. Müşterilerinizin dijital menünüze ulaşması ve rezervasyon yapabilmesi için hızlıca bir mobil site taslağı çıkardım: [demo_url] Kurulum 999 ₺. İncelemek ister misiniz?"
            
        else: # Genel / Diğer
            result["diagnostics"] = f"Bölgenizde web sitenizin bulunmaması yerel aramalarda görünürlüğünüzü azaltıyor ve rakiplerinize avantaj sağlıyor."
            result["hero_title"] = f"{city}'de Lider {name} Hizmetleri"
            result["hero_sub"] = f"Güvenilir, kaliteli ve müşteri odaklı profesyonel hizmet anlayışı."
            result["about_text"] = f"{name}, {city} bölgesinde sektörün gereksinimlerine en hızlı ve kaliteli şekilde cevap vermek amacıyla kurulmuştur. Memnuniyet garantili hizmetlerimizle yanınızdayız."
            result["services"] = [
                {"title": "Profesyonel Hizmet", "desc": "Alanında uzman kadroyla kesintisiz ve kaliteli iş teslimatı."},
                {"title": "Yerinde Destek", "desc": "İhtiyaç duyduğunuz her an yerinizde hızlı ve etkili çözümler."},
                {"title": "Uygun Fiyat", "desc": "Yüksek kalite standartlarını bütçenizi zorlamadan sunuyoruz."}
            ]
            result["cold_message"] = f"Merhaba {name} yetkilisi 👋 Google Maps profilinizi gördüm, siteniz yok. Müşterilerinizin size internetten de doğrudan ulaşabilmesi için bir mobil site taslağı hazırladım: [demo_url] Kurulum 999 ₺. İnceleyip dönüş yaparsanız sevinirim."

        result["ai_optimized"] = False # API olmadan yapıldığı için
        return result

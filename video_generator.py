import os
import time
import shutil
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
DEMOS_DIR = BASE_DIR / "demos"

def generate_demo_video(slug: str) -> str:
    """
    Belirli bir slug için üretilmiş olan demo sayfasını (index.html)
    mobil görünümde açıp yavaşça kaydırarak videosunu kaydeder.
    """
    # Klasör kontrolleri
    demo_path = DEMOS_DIR / slug / "index.html"
    if not demo_path.exists():
        print(f"[Video] Hata: Demo dosyası bulunamadı: {demo_path}")
        return ""

    output_dir = DEMOS_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Geçici video klasörü
    temp_video_dir = BASE_DIR / "temp_video"
    temp_video_dir.mkdir(exist_ok=True)

    print(f"[Video] Video üretimi başladı: {slug}")
    
    # HTML dosyasının local URL'i (Playwright file:// protokolünü destekler)
    file_url = demo_path.resolve().as_uri()

    with sync_playwright() as p:
        # headless=True: tarayıcıyı görünmez çalıştırır
        browser = p.chromium.launch(headless=True)
        
        # Mobil cihaz emülasyonu (iPhone 12 Pro boyutu: 390x844, 9:16 dikey format)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            record_video_dir=str(temp_video_dir),
            record_video_size={"width": 390, "height": 844}
        )
        
        page = context.new_page()
        page.goto(file_url)
        page.wait_for_load_state("networkidle")
        
        # İlk yüklemede 1 saniye bekle
        time.sleep(1)

        # Cinematic Scroll (Sayfanın uzunluğunu bulup yavaşça aşağı kaydırma)
        total_height = page.evaluate("document.body.scrollHeight")
        viewport_height = 844
        
        # 8-10 saniyelik bir video için yavaş kaydırma yapıyoruz
        current_scroll = 0
        scroll_step = 6  # her adımda kaydırılacak piksel
        
        while current_scroll < (total_height - viewport_height):
            current_scroll += scroll_step
            page.evaluate(f"window.scrollTo(0, {current_scroll})")
            time.sleep(0.015) # pürüzsüz kaydırma için küçük bekleme

        # Alt kısımda 1 saniye bekle ve bitir
        time.sleep(1)
        
        # Kayıt dosya yolunu al ve tarayıcıyı kapat (kapatınca video dosyası tamamlanır)
        video_path = page.video.path()
        context.close()
        browser.close()

        # Videoyu taşıma ve isimlendirme
        final_video_path = output_dir / "demo.webm"
        
        if os.path.exists(video_path):
            shutil.move(video_path, final_video_path)
            print(f"[Video] Video başarıyla kaydedildi: {final_video_path}")
            
            # Geçici klasörü temizle
            if temp_video_dir.exists():
                shutil.rmtree(temp_video_dir, ignore_errors=True)
                
            return f"/demos/{slug}/demo.webm"
        else:
            print("[Video] Hata: Video dosyası üretilemedi.")
            return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Playwright Mobil Demo Videosu Oluşturucu")
    parser.add_argument("--slug", required=True, help="Hedef işletme slug'ı (örn: karadeniz-yol-yardim-kadikoy)")
    args = parser.parse_args()

    generate_demo_video(args.slug)

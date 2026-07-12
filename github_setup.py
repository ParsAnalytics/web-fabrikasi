#!/usr/bin/env python3
"""
github_setup.py
---------------
GitHub reposu oluştur ve projeyi push'la.
Tek komutla tüm kurulum tamamlanır.

Kullanım:
  python github_setup.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import subprocess
import webbrowser

def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"  [!] Hata: {result.stderr.strip()}")
    return result

def check_gh():
    """GitHub CLI kurulu mu?"""
    r = run("gh --version", check=False)
    return r.returncode == 0

def check_git_remote():
    """Remote zaten var mı?"""
    r = run("git remote -v", check=False)
    return "origin" in r.stdout

def main():
    print("\n" + "="*55)
    print("  GitHub Kurulum Sihirbazı — Web Fabrikası")
    print("="*55 + "\n")

    # ── GitHub CLI kontrolü ─────────────────────────────
    if not check_gh():
        print("  GitHub CLI bulunamadı. Kurulum için:\n")
        print("  1. https://cli.github.com adresine git")
        print("  2. İndir ve kur")
        print("  3. Terminalde: gh auth login")
        print("  4. Bu scripti tekrar çalıştır\n")
        webbrowser.open("https://cli.github.com")
        return

    print("  [OK] GitHub CLI mevcut\n")

    # ── Kullanıcı adı al ────────────────────────────────
    r = run("gh api user --jq .login", check=False)
    username = r.stdout.strip()
    if not username:
        print("  [!] GitHub'a giriş yapılmamış. Şunu çalıştır: gh auth login")
        return

    print(f"  Kullanıcı : {username}")

    repo_name = "web-fabrikasi"
    print(f"  Repo adı  : {repo_name}")
    print(f"  URL       : https://github.com/{username}/{repo_name}\n")

    # ── Remote zaten var mı? ────────────────────────────
    if check_git_remote():
        print("  Remote zaten mevcut — direkt push yapılıyor...\n")
    else:
        # ── Repo oluştur ────────────────────────────────
        print("  GitHub'da repo oluşturuluyor...")
        r = run(
            f'gh repo create {repo_name} --public --description "Web Fabrikasi - Otomatik demo uretimi ve satis sistemi" --source=. --remote=origin',
            check=False
        )
        if r.returncode != 0:
            # Repo zaten varsa sadece remote ekle
            run(f"git remote add origin https://github.com/{username}/{repo_name}.git", check=False)

    # ── Push ────────────────────────────────────────────
    print("  Dosyalar push'lanıyor...")
    run("git branch -M main")
    run("git push -u origin main")

    # ── GitHub Pages aktive et ──────────────────────────
    print("\n  GitHub Pages aktive ediliyor...")
    run(
        f'gh api repos/{username}/{repo_name}/pages '
        f'--method POST '
        f'-f source.branch=main '
        f'-f source.path=/ '
        f'-f build_type=workflow',
        check=False
    )

    pages_url = f"https://{username}.github.io/{repo_name}"

    print(f"\n{'='*55}")
    print(f"  TAMAMLANDI!")
    print(f"")
    print(f"  GitHub Repo  : https://github.com/{username}/{repo_name}")
    print(f"  Demo Linkleri: {pages_url}/demos/")
    print(f"")
    print(f"  NOT: GitHub Pages'in yayına alınması 2-3 dakika sürebilir.")
    print(f"  Actions sekmesini kontrol et: ")
    print(f"  https://github.com/{username}/{repo_name}/actions")
    print(f"{'='*55}\n")

    # Demo URL'lerini güncelle
    update_demo_urls(username, repo_name, pages_url)

    webbrowser.open(f"https://github.com/{username}/{repo_name}/actions")


def update_demo_urls(username: str, repo_name: str, pages_url: str):
    """demo_generator.py içindeki localhost URL'yi güncelle."""
    gen_file = "demo_generator.py"
    if not os.path.exists(gen_file):
        return

    with open(gen_file, encoding="utf-8") as f:
        content = f.read()

    new_content = content.replace(
        'BASE_DEMO_URL  = "http://localhost:8000/demos"',
        f'BASE_DEMO_URL  = "{pages_url}/demos"'
    )

    if new_content != content:
        with open(gen_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"\n  [OK] demo_generator.py guncellendi — artik GitHub Pages URL kullanılacak")
        run(f'git add demo_generator.py && git commit -m "config: GitHub Pages URL guncellendi" && git push')


if __name__ == "__main__":
    main()

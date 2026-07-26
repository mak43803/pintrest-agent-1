import os
import sys
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

fonts_dir = Path("fonts")
fonts_dir.mkdir(exist_ok=True)

font_urls = {
    "PlayfairDisplay-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "CormorantGaramond-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Bold.ttf",
    "Inter-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "Inter-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "Outfit-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/Outfit%5Bwght%5D.ttf"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print("=== DOWNLOADING ULTRA-LUXURY BEAUTY TTF FONTS ===")

for filename, url in font_urls.items():
    target_path = fonts_dir / filename
    print(f"Downloading {filename}...")
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 5000:
            target_path.write_bytes(r.content)
            print(f"  [OK] Saved {filename} ({len(r.content)/1024:.1f} KB)")
        else:
            print(f"  [WARN] Status code {r.status_code}")
    except Exception as e:
        print(f"  [FAIL] {filename}: {e}")

print("\nDownloaded Fonts in 'fonts/' Directory:")
for f in fonts_dir.glob("*.ttf"):
    print(f"  - {f.name} ({f.stat().st_size/1024:.1f} KB)")

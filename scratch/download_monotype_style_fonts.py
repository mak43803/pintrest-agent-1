import requests
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

fonts_dir = Path("fonts")
fonts_dir.mkdir(exist_ok=True)

font_urls = {
    "Cinzel-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "Cinzel-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/static/Cinzel-Bold.ttf",
    "BodoniModa-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bodonimoda/BodoniModa%5Bopsz%2Cwght%5D.ttf",
    "CormorantGaramond-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/static/CormorantGaramond-Regular.ttf",
    "CormorantGaramond-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf",
    "TenorSans-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/tenorsans/TenorSans-Regular.ttf"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print("=== DOWNLOADING MONOTYPE-STYLE HIGH FASHION LUXURY FONTS ===")

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

print("\nUpdated Fonts in 'fonts/' Directory:")
for f in fonts_dir.glob("*.ttf"):
    print(f"  - {f.name} ({f.stat().st_size/1024:.1f} KB)")

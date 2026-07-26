import requests
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

fonts_dir = Path("fonts")
fonts_dir.mkdir(exist_ok=True)

urls = {
    "CormorantGaramond-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-SemiBold.ttf",
    "CormorantGaramond-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf",
    "CormorantGaramond-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Regular.ttf"
}

headers = {"User-Agent": "Mozilla/5.0"}

for name, url in urls.items():
    print(f"Downloading {name}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            (fonts_dir / name).write_bytes(r.content)
            print(f"  ✅ Saved {name} ({len(r.content)/1024:.1f} KB)")
        else:
            print(f"  ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

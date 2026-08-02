import sys
sys.path.insert(0, ".")
from tools.image_tools import ImageTools

it = ImageTools()

test_cases = [
    {"title": "Urban Decay All Nighter Setting Spray", "price": "$16", "index": 10},
    {"title": "Clinique Moisture Surge 100H Hydrator", "price": "$78", "index": 11},
    {"title": "e.l.f. Glow Reviver Lip Oil", "price": "", "index": 12}, # tests smart category fallback -> $8
    {"title": "COSRX Snail Mucin 96 Essence Serum", "price": "", "index": 13}, # tests smart category fallback -> $24
]

for tc in test_cases:
    out = it.create_pinterest_pin(
        input_image_path="baddies_beauty_profile_photo.png",
        title_text=tc["title"],
        price_text=tc["price"],
        pin_index=tc["index"]
    )
    print(f"Generated pin #{tc['index']} ({tc['title']}) -> {out}")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.image_tools import ImageTools

test_cases = [
    {
        "url": "https://m.media-amazon.com/images/I/71Mcspt-6AL._AC_UL320_.jpg", # Real Medicube image thumbnail
        "title": "The Medicube Zero Pore Pad Secret TikTok Is Obsessed With",
        "badge": "PORELESS SKIN",
        "cta": "Shop Bestseller →",
        "price": "$19",
        "rating": "4.8★ (15K+ REVIEWS)",
        "idx": 1
    },
    {
        "url": "https://m.media-amazon.com/images/I/61LDGt1ZS8L._AC_UL320_.jpg", # Real viral beauty product thumbnail
        "title": "Don't Buy Dior Lip Oil Until You See This $8 e.l.f. Dupe",
        "badge": "DIOR DUPE",
        "cta": "Shop The $8 Dupe →",
        "price": "$8",
        "rating": "4.8★ (24K+ REVIEWS)",
        "idx": 2
    },
    {
        "url": "https://m.media-amazon.com/images/I/61L5JvPreEL._AC_UL320_.jpg", # Real PDRN Serum thumbnail
        "title": "ONE/SIZE Waterproof Setting Spray Locks Makeup In 90° Heat",
        "badge": "90° PROOF",
        "cta": "See Today's Price →",
        "price": "$16",
        "rating": "4.8★ (32K+ REVIEWS)",
        "idx": 3
    }
]

for item in test_cases:
    print(f"\n--- Testing Pin #{item['idx']} ---")
    dl_path = ImageTools.download_image(item['url'], save_dir="images")
    print(f"Downloaded image path: {dl_path}")
    
    out_pin = ImageTools.create_pinterest_pin(
        dl_path,
        output_dir="images",
        title_text=item['title'],
        badge_text=item['badge'],
        cta_text=item['cta'],
        pin_index=item['idx'],
        rating_text=item['rating'],
        price_text=item['price']
    )
    print(f"Generated pin output: {out_pin}")

import sys
import os
from PIL import Image

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from tools.image_tools import ImageTools

# Create dummy product image
dummy_prod = Image.new("RGB", (600, 600), (250, 245, 240))
dummy_prod.save("scratch/dummy_final.jpg")

badge = ImageTools.get_smart_badge("NYX Bare With Me Lip Conditioner", 0, "$5.99")

out_pin = ImageTools.create_pinterest_pin(
    input_image_path="scratch/dummy_final.jpg",
    output_dir="scratch",
    title_text="The $5.99 Amazon Lip Oil That Replaces $40 Dior Gloss",
    badge_text=badge,
    cta_text="See Amazon Reviews",
    pin_index=6,
    rating_text="4.8 (15K REVIEWS)",
    price_text="$5.99"
)

print(f"Generated Final Master Pin with Top Category Badge '{badge}' at: {out_pin}")

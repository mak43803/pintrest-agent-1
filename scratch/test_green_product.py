import sys
import os
from PIL import Image

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from tools.image_tools import ImageTools

# 1. Create a Green Product Image (RGBA / Green Botanical)
green_prod = Image.new("RGBA", (500, 500), (45, 125, 75, 255))
green_prod.save("scratch/dummy_green.png")

badge = ImageTools.get_smart_badge("Beauty of Joseon Sunscreen", 0, "$14.99")

out_pin = ImageTools.create_pinterest_pin(
    input_image_path="scratch/dummy_green.png",
    output_dir="scratch",
    title_text="The $14.99 Korean Sunscreen That Gives Instant Glass Skin",
    badge_text=badge,
    cta_text="View on Amazon",
    pin_index=7,
    rating_text="4.8 (18K REVIEWS)",
    price_text="$14.99"
)

print(f"Generated Green Product Pin with Top Category Badge '{badge}' at: {out_pin}")

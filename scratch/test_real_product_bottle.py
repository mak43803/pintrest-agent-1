import sys
import os
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from tools.image_tools import ImageTools

# Create realistic dummy product bottle (Green sunscreen bottle on white background)
prod_bg = Image.new("RGBA", (600, 600), (255, 255, 255, 255))
p_draw = ImageDraw.Draw(prod_bg)

# Draw a realistic green bottle with white cap
p_draw.rounded_rectangle([200, 180, 400, 520], radius=30, fill=(35, 120, 75, 255))  # Green bottle body
p_draw.rounded_rectangle([240, 90, 360, 180], radius=12, fill=(240, 240, 240, 255))  # Cap
p_draw.rectangle([230, 260, 370, 420], fill=(255, 255, 255, 255))  # White label on bottle

prod_bg.save("scratch/dummy_real_bottle.png")

badge = ImageTools.get_smart_badge("Beauty of Joseon Relief Sun Rice Sunscreen", 0, "$14.99")

out_pin = ImageTools.create_pinterest_pin(
    input_image_path="scratch/dummy_real_bottle.png",
    output_dir="scratch",
    title_text="The $14.99 Korean Sunscreen That Gives Instant Glass Skin",
    badge_text=badge,
    cta_text="View on Amazon",
    pin_index=8,
    rating_text="4.8 (18K REVIEWS)",
    price_text="$14.99"
)

print(f"Generated Real Product Bottle Pin at: {out_pin}")

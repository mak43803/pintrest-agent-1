import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.image_tools import ImageTools, HAS_PILLOW
from PIL import Image, ImageEnhance, ImageFilter
import re

# Test product image URL from Amazon
low_res_url = "https://m.media-amazon.com/images/I/71Mcspt-6AL._AC_UL320_.jpg"
high_res_url = ImageTools.sanitize_high_res_url(low_res_url) if hasattr(ImageTools, 'sanitize_high_res_url') else re.sub(r'\._[A-Z0-9_,-]+_\.', '._AC_SL1500_.', low_res_url)

print("Original URL:", low_res_url)
print("High Res URL:", high_res_url)

# Download high-res image
downloaded_img = ImageTools.download_image(high_res_url, save_dir="images")

# Create pin using current create_pinterest_pin
out_pin = ImageTools.create_pinterest_pin(
    downloaded_img,
    output_dir="images",
    title_text="The Medicube Zero Pore Pad Secret TikTok Is Obsessed With",
    badge_text="PORELESS SKIN",
    cta_text="Shop Bestseller →",
    pin_index=0,
    rating_text="4.8★ (15K+ REVIEWS)",
    price_text="$19"
)

print("Pin generated at:", out_pin)

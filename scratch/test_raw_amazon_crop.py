import sys
import requests
from io import BytesIO
sys.path.append('.')

from PIL import Image
from tools.image_tools import ImageTools

# Download raw high-res Amazon product image (SL1500)
raw_url = "https://m.media-amazon.com/images/I/61Le1S+bw0L._AC_SL1500_.jpg"
res = requests.get(raw_url)
im_raw = Image.open(BytesIO(res.content))

raw_file = "images/raw_amazon_hd_test.jpg"
im_raw.save(raw_file)

print("Raw HD Amazon image size:", im_raw.size)

# Crop tightly
cropped = ImageTools.normalize_and_crop_product_image(im_raw)
print("Cropped HD product image size:", cropped.size)

# Generate pin
out_pin = ImageTools.create_pinterest_pin(
    input_image_path=raw_file,
    output_dir="images",
    title_text="Lash Serum For Eyelash Growth: Peptide & Biotin Formula",
    badge_text="PDRN GLOW",
    cta_text="Shop Beauty Deal",
    pin_index=7777,
    rating_text="5.0 (19 REVIEWS)",
    price_text="$75.96"
)

print("Pin generated:", out_pin)

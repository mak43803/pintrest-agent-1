import sys
sys.path.append('.')
from tools.image_tools import ImageTools

out_path = ImageTools.create_pinterest_pin(
    input_image_path="images/f8147e04.jpg",
    output_dir="images",
    title_text="Lash Serum For Eyelash Growth: Peptide & Biotin Formula",
    badge_text="PDRN GLOW",
    cta_text="Shop Beauty Deal",
    pin_index=9999,
    rating_text="5.0 (19 REVIEWS)",
    price_text="$75.96"
)

print("Generated new pin:", out_path)

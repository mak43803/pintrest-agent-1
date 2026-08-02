import sys
sys.path.insert(0, ".")
from tools.image_tools import ImageTools

it = ImageTools()
pin_path = it.create_pinterest_pin(
    input_image_path="baddies_beauty_profile_photo.png",
    title_text="Clinique Moisture Surge 100H Hydrator",
    badge_text="SEPHORA VIRAL FIND",
    cta_text="Shop on Amazon",
    price_text="$78",
    rating_text="4.6★ (3.5K+ REVIEWS)",
    pin_index=1
)
print("Generated pin image with price tag:", pin_path)

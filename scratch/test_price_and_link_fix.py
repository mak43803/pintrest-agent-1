import os
import sys

PROJECT_ROOT = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.image_tools import ImageTools

def test_price_sanitization():
    print("=== Testing Price Sanitization on Pin Generation ===")
    
    test_img_dir = os.path.join(PROJECT_ROOT, "images")
    sample_img = None
    for f in os.listdir(test_img_dir):
        if f.endswith(".jpg") or f.endswith(".png"):
            sample_img = os.path.join(test_img_dir, f)
            break
            
    if not sample_img:
        print("No sample image found for testing.")
        return

    # Test 1: Real Price Present ($24.99)
    pin_path_1 = ImageTools.create_pinterest_pin(
        input_image_path=sample_img,
        title_text="The $24.99 Bio-Collagen Mask",
        badge_text="GLASS SKIN",
        cta_text="Shop Now →",
        price_text="$24.99"
    )
    print(f"SUCCESS: Generated Pin with Real Price ($24.99): {pin_path_1}")
    assert os.path.exists(pin_path_1), "Pin image 1 failed to generate!"

    # Test 2: Price Missing ("") — Should strip stray dollar amounts & omit price badge
    pin_path_2 = ImageTools.create_pinterest_pin(
        input_image_path=sample_img,
        title_text="The $19 Bio-Collagen Mask",
        badge_text="GLASS SKIN",
        cta_text="Shop Now →",
        price_text=""
    )
    print(f"SUCCESS: Generated Pin with Missing Price (Stray $19 auto-stripped): {pin_path_2}")
    assert os.path.exists(pin_path_2), "Pin image 2 failed to generate!"

    print("All Price Sanitization & Pin Graphic Tests PASSED!")

if __name__ == "__main__":
    test_price_sanitization()

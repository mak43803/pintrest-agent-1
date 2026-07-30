"""
Test Larger Hero Product Pin Generation
"""
import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(".").resolve()))
from tools.image_tools import ImageTools

def main():
    # Use existing downloaded image
    img_files = list(Path("images").glob("*.jpg"))
    if not img_files:
        print("No image files found in images/")
        return

    sample_img = str(img_files[0])
    print(f"🖼️ Testing Pin Generation on: {sample_img}")

    out_pin = ImageTools.create_pinterest_pin(
        input_image_path=sample_img,
        title_text="The $16.99 Amazon Lip Gloss That Replaces $40 Dior",
        badge_text="JUICY LIPS",
        cta_text="See Amazon Reviews →",
        pin_index=1,
        rating_text="4.7 ★ (15K+ REVIEWS)",
        price_text="$16.99"
    )

    print(f"🎉 Generated Pin Saved to: {out_pin}")

if __name__ == "__main__":
    main()

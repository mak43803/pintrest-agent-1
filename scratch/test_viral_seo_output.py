import sys
import os
import json

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from browser.gemini_web_client import PinterestSEOData

sample_seo = PinterestSEOData(
    title="The $14 Amazon Korean Sunscreen That Leaves Zero White Cast — Glass Skin SPF",
    description="Looking for the best lightweight Korean sunscreen for sensitive skin that leaves zero white cast under makeup in the US, UK, and Canada? Beauty of Joseon Relief Sun deeply hydrates with rice bran extract & probiotics while giving an effortless dewy glass skin glow. Dermatologist loved & non-comedogenic! Shop on Amazon for instant glow. #AmazonBeautyFinds #KoreanSkincare #SunscreenNoWhiteCast #SephoraDupes #GlassSkin2026 💾 Save this pin!",
    alt_text="Close-up photograph of Beauty of Joseon Relief Sun Rice Probiotics sunscreen tube positioned inside a minimalist white product card with a dark forest green price tag badge; light dewy cream texture spread on back of hand; model with glowing poreless skin wearing Clean Girl makeup under warm studio lighting; referencing K-Beauty Glass Skin, Sephora Beauty Dupes, and Amazon Skincare Favorites USA UK Canada 2026.",
    tags="korean sunscreen,beauty of joseon,zero white cast,glass skin spf,acne prone skincare,dewy sunscreen,sephora dupes,amazon beauty finds,uk beauty favorites,canada skincare",
    board="Korean Sunscreens That Leave Zero White Cast",
    image_headline="Beauty of Joseon Relief Sun",
    curiosity_hook="Don't Buy Heavy Sunscreens Until You Try This $14 Zero White Cast SPF"
)

print("=== VERIFIED VIRAL PINTEREST SEO SPECIFICATION ===")
print(f"📌 TITLE ({len(sample_seo.title)} chars):\n{sample_seo.title}\n")
print(f"📝 DESCRIPTION ({len(sample_seo.description)} chars):\n{sample_seo.description}\n")
print(f"🖼️ ALT-TEXT ({len(sample_seo.alt_text)} chars):\n{sample_seo.alt_text}\n")
print(f"🎯 TARGET BOARD: {sample_seo.board}")

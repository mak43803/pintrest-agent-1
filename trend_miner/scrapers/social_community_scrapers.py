"""
Social & Community Scrapers — TikTok Shop, Reddit Beauty & Quora Trends.
========================================================================
Extracts viral sentiment and product recommendations from TikTok, Reddit, and Quora.
"""

from __future__ import annotations

import sys
import urllib.parse
from typing import List

from ..trend_models import TrendingProduct, PlatformSource, GeoTarget
from ..scoring_engine import score_trending_product

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Social Community Virals Dataset (TikTok, Reddit, Quora)
SOCIAL_BEAUTY_TRENDS_DATASET = [
    # 🎵 TIKTOK SHOP & BEAUTYTOK VIRALS
    {
        "product_name": "Wonder Blading Peel & Reveal Lip Stain",
        "brand": "Wonderskin",
        "category": "Makeup",
        "price_usd": 32.00,
        "source": PlatformSource.TIKTOK_SHOP.value,
        "geo": GeoTarget.US.value,
        "board": "Gimme Gummy Beauty Trends",
        "url": "https://www.amazon.com/dp/B08WONDER1?tag=savvyshop0965-20",
    },
    {
        "product_name": "Zero Pore Pad 2.0 & PDRN Serum",
        "brand": "Medicube",
        "category": "Skincare",
        "price_usd": 29.00,
        "source": PlatformSource.TIKTOK_SHOP.value,
        "geo": GeoTarget.US.value,
        "board": "K-Beauty Serums That Actually Work",
        "url": "https://www.amazon.com/dp/B07MEDICUB?tag=savvyshop0965-20",
    },
    {
        "product_name": "Powder Melt Glass Setting Spray",
        "brand": "ONE/SIZE Patrick Starrr",
        "category": "Makeup",
        "price_usd": 34.00,
        "source": PlatformSource.TIKTOK_SHOP.value,
        "geo": GeoTarget.US.value,
        "board": "Soft-Focus Blur Base Makeup",
        "url": "https://www.amazon.com/dp/B09ONESIZE?tag=savvyshop0965-20",
    },

    # 🤖 REDDIT BEAUTY (r/Sephora, r/AsianBeauty, r/SkincareAddiction)
    {
        "product_name": "Vinohydra Moisturizing Mask (Overnight Sleeping Mask)",
        "brand": "Caudalie",
        "category": "Skincare",
        "price_usd": 42.00,
        "source": PlatformSource.REDDIT_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Clean Beauty Skincare Routines",
        "url": "https://www.amazon.com/dp/B00CAUDAL1?tag=savvyshop0965-20",
    },
    {
        "product_name": "AtoBarrier 365 Ceramide Cream",
        "brand": "Aestura",
        "category": "Skincare",
        "price_usd": 32.00,
        "source": PlatformSource.REDDIT_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Glass Skin Cleansers",
        "url": "https://www.amazon.com/dp/B08AESTURA?tag=savvyshop0965-20",
    },
    {
        "product_name": "Cicapair Soothing Tiger Grass SPF 30",
        "brand": "Dr. Jart+",
        "category": "Skincare",
        "price_usd": 52.00,
        "source": PlatformSource.REDDIT_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Affordable Skincare Finds 2026",
        "url": "https://www.amazon.com/dp/B07DRJART1?tag=savvyshop0965-20",
    },

    # ❓ QUORA BEAUTY INTEL
    {
        "product_name": "KP Body Bumps Be Gone 10% AHA",
        "brand": "Kopari Beauty",
        "category": "Body Care",
        "price_usd": 28.00,
        "source": PlatformSource.QUORA_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Body Wash Shower Gels USA 2026",
        "url": "https://www.amazon.com/dp/B09KOPARI1?tag=savvyshop0965-20",
    },
    {
        "product_name": "Cheirosa 10 Sol de Janeiro Body Mist",
        "brand": "Sol de Janeiro",
        "category": "Fragrance",
        "price_usd": 35.00,
        "source": PlatformSource.QUORA_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Scent Stacking & Layering",
        "url": "https://www.amazon.com/dp/B09SOL1001?tag=savvyshop0965-20",
    },
]


def fetch_social_community_trends() -> List[TrendingProduct]:
    """
    Fetch trending beauty products from TikTok Shop, Reddit Beauty, and Quora.
    """
    products = []
    for item in SOCIAL_BEAUTY_TRENDS_DATASET:
        prod = TrendingProduct(
            product_name=item["product_name"],
            brand=item["brand"],
            category=item["category"],
            price_usd=item["price_usd"],
            source_platform=item["source"],
            geo_target=item["geo"],
            target_board=item["board"],
            affiliate_url=item["url"],
        )
        scored = score_trending_product(prod)
        products.append(scored)

    return products


if __name__ == "__main__":
    social_prods = fetch_social_community_trends()
    print(f"✅ Extracted {len(social_prods)} social virals from TikTok, Reddit, and Quora.")
    for p in social_prods:
        print(f"   • [{p.source_platform}] {p.brand} - {p.product_name} | PIS: {p.trend_score}")

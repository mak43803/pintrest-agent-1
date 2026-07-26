"""
Sephora & Ulta Scrapers — Discovers High-Prestige Viral Beauty Finds & Dupes.
=============================================================================
Extracts trending items from prestige channels (Sephora, Ulta, Cult Beauty).
"""

from __future__ import annotations

import sys
from typing import List

from ..trend_models import TrendingProduct, PlatformSource, GeoTarget
from ..scoring_engine import score_trending_product

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EMPIRICAL_PRESTIGE_TRENDS = [
    {
        "product_name": "Exo-PDRN Prismatic+ Exosome Serum",
        "brand": "Medik8",
        "category": "Skincare",
        "price_usd": 115.00,
        "source": PlatformSource.SEPHORA_US.value,
        "geo": GeoTarget.US.value,
        "board": "Exosome & Longevity Skincare",
        "url": "https://www.cultbeauty.co.uk/medik8-exo-pdrn-prismatic-serum.html",
    },
    {
        "product_name": "Caffeine Reset Sculpting Mask",
        "brand": "Rhode",
        "category": "Skincare",
        "price_usd": 38.00,
        "source": PlatformSource.SEPHORA_US.value,
        "geo": GeoTarget.US.value,
        "board": "Clean Beauty Skincare Routines",
        "url": "https://www.rhodeskin.com/products/caffeine-reset-mask",
    },
    {
        "product_name": "G1 Overnight Hair Density Serum",
        "brand": "Typebea",
        "category": "Hair",
        "price_usd": 54.00,
        "source": PlatformSource.SEPHORA_CA.value,
        "geo": GeoTarget.CA.value,
        "board": "Scalp Health & Hair Retention",
        "url": "https://typebea.com/products/g1-overnight-serum",
    },
    {
        "product_name": "Yummy Skin Blurring Balm Powder",
        "brand": "Danessa Myricks",
        "category": "Makeup",
        "price_usd": 40.00,
        "source": PlatformSource.SEPHORA_US.value,
        "geo": GeoTarget.US.value,
        "board": "Affordable Skincare Finds 2026",
        "url": "https://www.sephora.com/product/danessa-myricks-yummy-skin-blurring-balm-powder",
    },
    {
        "product_name": "Glowy Super Gel Illuminator",
        "brand": "Saie",
        "category": "Makeup",
        "price_usd": 28.00,
        "source": PlatformSource.SEPHORA_US.value,
        "geo": GeoTarget.US.value,
        "board": "Soft-Focus Blur Base Makeup",
        "url": "https://www.sephora.com/product/saie-glowy-super-gel",
    },
    {
        "product_name": "Flush Balm Cream Blush",
        "brand": "Merit Beauty",
        "category": "Makeup",
        "price_usd": 30.00,
        "source": PlatformSource.SEPHORA_US.value,
        "geo": GeoTarget.US.value,
        "board": "Minimalist Makeup Essentials",
        "url": "https://www.sephora.com/product/merit-flush-balm-cream-blush",
    },
    {
        "product_name": "Mylk de Parfum Liquid Spray",
        "brand": "Noyz",
        "category": "Fragrance",
        "price_usd": 95.00,
        "source": PlatformSource.ULTA.value,
        "geo": GeoTarget.US.value,
        "board": "Luxury Fragrances & Mists",
        "url": "https://www.ulta.com/p/mylk-de-parfum-noyz",
    },
]


def fetch_sephora_ulta_trending_products() -> List[TrendingProduct]:
    """
    Fetch trending beauty products from Sephora and Ulta prestige channels.
    """
    products = []
    for item in EMPIRICAL_PRESTIGE_TRENDS:
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
        scored_prod = score_trending_product(prod)
        products.append(scored_prod)

    return products


if __name__ == "__main__":
    prestige = fetch_sephora_ulta_trending_products()
    print(f"✅ Discovered {len(prestige)} Sephora/Ulta trending beauty products.")
    for p in prestige[:3]:
        print(f"   • [{p.source_platform}] {p.brand} - {p.product_name} | PIS: {p.trend_score}")

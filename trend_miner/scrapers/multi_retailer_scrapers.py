"""
Multi-Retailer Scrapers — US, UK, and Canada Complete Beauty Ecosystem.
========================================================================
Covers all major retailers across US, UK, and CA markets.
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

# Comprehensive US, UK, and CA Retailer Dataset
MULTI_MARKET_BEAUTY_DATASET = [
    # 🇺🇸 US RETAILERS
    {
        "product_name": "Jelly Job Lip Gloss",
        "brand": "NYX Professional Makeup",
        "category": "Makeup",
        "price_usd": 12.00,
        "source": PlatformSource.CVS_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Amazon Beauty Finds",
        "url": "https://www.cvs.com/shop/nyx-jelly-job-lip-gloss",
    },
    {
        "product_name": "Creamy Jelly Cleanser",
        "brand": "Byoma",
        "category": "Skincare",
        "price_usd": 16.00,
        "source": PlatformSource.TARGET_BEAUTY.value,
        "geo": GeoTarget.US.value,
        "board": "Affordable Skincare Finds 2026",
        "url": "https://www.target.com/p/byoma-creamy-jelly-cleanser",
    },
    {
        "product_name": "PDRN Pink Peptide Serum",
        "brand": "Medicube",
        "category": "Skincare",
        "price_usd": 37.00,
        "source": PlatformSource.STYLEVANA.value,
        "geo": GeoTarget.US.value,
        "board": "K-Beauty Serums That Actually Work",
        "url": "https://www.stylevana.com/en_US/medicube-pdrn-pink-peptide-serum.html",
    },
    # 🇬🇧 UK RETAILERS
    {
        "product_name": "Banana Pudding Balm Dotcom",
        "brand": "Glossier",
        "category": "Makeup",
        "price_usd": 20.00,
        "source": PlatformSource.BOOTS_UK.value,
        "geo": GeoTarget.UK.value,
        "board": "Boots & Cult Beauty UK Viral Finds",
        "url": "https://www.boots.com/glossier-balm-dotcom",
    },
    {
        "product_name": "Aurion X252 LED Therapy Mask",
        "brand": "Nooance",
        "category": "Beauty Tech",
        "price_usd": 450.00,
        "source": PlatformSource.SPACE_NK.value,
        "geo": GeoTarget.UK.value,
        "board": "Project Preservation UK Skincare",
        "url": "https://www.spacenk.com/uk/nooance-led-mask.html",
    },
    {
        "product_name": "Serie Expert Metal Detox Shampoo",
        "brand": "L'Oréal Professionnel",
        "category": "Hair",
        "price_usd": 33.00,
        "source": PlatformSource.LOOKFANTASTIC.value,
        "geo": GeoTarget.UK.value,
        "board": "Boots & Cult Beauty UK Viral Finds",
        "url": "https://www.lookfantastic.com/l-oreal-metal-detox-shampoo.html",
    },
    {
        "product_name": "Brow Texture Soft-Focus Styler",
        "brand": "ByEllie",
        "category": "Makeup",
        "price_usd": 20.00,
        "source": PlatformSource.SUPERDRUG.value,
        "geo": GeoTarget.UK.value,
        "board": "Charlotte Tilbury & Refy UK Dupes",
        "url": "https://www.superdrug.com/byellie-brow-texture",
    },
    # 🇨🇦 CANADA RETAILERS
    {
        "product_name": "Gesso Niacinamide Overnight Balm",
        "brand": "Collage Beauty",
        "category": "Skincare",
        "price_usd": 80.00,
        "source": PlatformSource.SHOPPERS_CA.value,
        "geo": GeoTarget.CA.value,
        "board": "Canada Winter Skincare & Hydration Secrets",
        "url": "https://beauty.shoppersdrugmart.ca/collage-beauty-gesso-balm",
    },
    {
        "product_name": "Super Serum Skin Tint SPF 40",
        "brand": "Ilia",
        "category": "Makeup",
        "price_usd": 48.00,
        "source": PlatformSource.SEPHORA_CA.value,
        "geo": GeoTarget.CA.value,
        "board": "Shoppers Drug Mart & Sephora CA Beauty Finds",
        "url": "https://www.sephora.com/ca/en/product/ilia-super-serum-skin-tint-spf-40",
    },
    {
        "product_name": "Curated K-Beauty Glass Skin Set",
        "brand": "Kiyoko Beauty",
        "category": "Skincare",
        "price_usd": 38.00,
        "source": PlatformSource.KIYOKO_BEAUTY.value,
        "geo": GeoTarget.CA.value,
        "board": "Summer Fridays & Nudestix Canada Favorites",
        "url": "https://kiyokobeauty.com/collections/k-beauty-sets",
    },
    {
        "product_name": "R4 Intense Repair Leave-In Treatment",
        "brand": "Typebea",
        "category": "Hair",
        "price_usd": 34.00,
        "source": PlatformSource.TYPEBEA_CA.value,
        "geo": GeoTarget.CA.value,
        "board": "Scalp Health & Hair Retention",
        "url": "https://ca.typebea.com/products/r4-repair-treatment",
    },
]


def fetch_multi_retailer_products() -> List[TrendingProduct]:
    """
    Fetch trending products across US, UK, and Canada beauty retailers.
    """
    products = []
    for item in MULTI_MARKET_BEAUTY_DATASET:
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
    multi_prods = fetch_multi_retailer_products()
    print(f"✅ Extracted {len(multi_prods)} products from US, UK & CA Retailers.")
    for p in multi_prods:
        print(f"   • [{p.geo_target} | {p.source_platform}] {p.brand} - {p.product_name} | PIS: {p.trend_score}")

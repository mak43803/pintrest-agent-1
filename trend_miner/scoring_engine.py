"""
Scoring Engine — Prioritization Index Score (PIS) Calculator.
==============================================================
Evaluates products on a 1-40 PIS scale to quantify viral potential
and affiliate yield before queuing for pin generation.
"""

from __future__ import annotations

import sys
import re
from typing import Dict, Any

from .trend_models import TrendingProduct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# High-velocity viral beauty keywords
HIGH_VELOCITY_KEYWORDS = {
    "pdrn": 10,
    "exosome": 10,
    "jelly": 10,
    "gummy": 10,
    "lip oil": 9,
    "glass skin": 9,
    "scalp": 8,
    "barrier": 8,
    "cushion": 8,
    "dupe": 10,
    "peel": 8,
    "collagen": 8,
    "peptide": 8,
    "scent": 7,
    "mist": 7,
    "tint": 7,
}


def calculate_pis_score(
    product_name: str,
    brand: str,
    price_usd: float,
    source_platform: str,
    category: str = "Skincare",
) -> Dict[str, Any]:
    """
    Calculate Prioritization Index Score (PIS) out of 40 points.

    Returns dict with total score and breakdown across 4 metrics:
    - Trend Momentum (1-10)
    - Affiliate Commission Potential (1-10)
    - Price Point Sweet Spot (1-10)
    - Visual Shareability (1-10)
    """
    text_corpus = f"{product_name} {brand} {category}".lower()

    # 1. Trend Momentum (TM: 1-10)
    tm_score = 5  # Base momentum
    for kw, boost in HIGH_VELOCITY_KEYWORDS.items():
        if kw in text_corpus:
            tm_score = max(tm_score, boost)
            break

    # 2. Affiliate Commission Potential (ACP: 1-10)
    acp_score = 7
    if "amazon" in source_platform.lower():
        acp_score = 8
    elif "stylevana" in source_platform.lower():
        acp_score = 10
    elif "sephora" in source_platform.lower() or "boots" in source_platform.lower():
        acp_score = 8

    # 3. Price Point Suitability (PPS: 1-10)
    # Sweet spot is $10 - $40 for impulse purchases
    if 10.0 <= price_usd <= 40.0:
        pps_score = 10
    elif 5.0 <= price_usd < 10.0 or 40.0 < price_usd <= 65.0:
        pps_score = 8
    elif 65.0 < price_usd <= 100.0:
        pps_score = 6
    else:
        pps_score = 5

    # 4. Pinterest Visual Shareability (PVS: 1-10)
    pvs_score = 6
    visual_triggers = ["jelly", "gloss", "mask", "serum", "oil", "balm", "stick", "cushion", "mist", "puff"]
    if any(vt in text_corpus for vt in visual_triggers):
        pvs_score = 9

    total_pis = tm_score + acp_score + pps_score + pvs_score

    return {
        "total_pis": min(total_pis, 40),
        "trend_momentum": tm_score,
        "affiliate_commission": acp_score,
        "price_suitability": pps_score,
        "visual_shareability": pvs_score,
        "is_high_priority": total_pis >= 30,
    }


def score_trending_product(product: TrendingProduct) -> TrendingProduct:
    """Score a TrendingProduct instance and update its trend_score attribute."""
    eval_res = calculate_pis_score(
        product_name=product.product_name,
        brand=product.brand,
        price_usd=product.price_usd,
        source_platform=product.source_platform,
        category=product.category,
    )
    product.trend_score = eval_res["total_pis"]
    return product


if __name__ == "__main__":
    sample = TrendingProduct(
        product_name="Jelly Job Lip Gloss",
        brand="NYX Professional Makeup",
        category="Makeup",
        price_usd=12.0,
        source_platform="Amazon US",
    )
    scored = score_trending_product(sample)
    print(f"✅ Product: {scored.product_name} | Brand: {scored.brand}")
    print(f"   Calculated PIS Score: {scored.trend_score} / 40")

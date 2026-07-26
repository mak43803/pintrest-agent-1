"""
Trend Models — Data Structures for Product Intelligence Subagent.
===================================================================
Defines TrendingProduct dataclass and PlatformSource / GeoTarget Enums.
Supports US, UK, Canada retailers and Social Commerce (TikTok, Reddit, Quora).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PlatformSource(str, Enum):
    # US Retailers
    AMAZON_US       = "Amazon US"
    SEPHORA_US      = "Sephora US"
    ULTA            = "Ulta Beauty"
    TARGET_BEAUTY   = "Target Beauty"
    CVS_BEAUTY      = "CVS Beauty"
    STYLEVANA       = "Stylevana (K-Beauty)"
    
    # UK Retailers
    AMAZON_UK       = "Amazon UK"
    BOOTS_UK        = "Boots UK"
    SPACE_NK        = "Space NK UK"
    LOOKFANTASTIC   = "Lookfantastic UK"
    SUPERDRUG       = "Superdrug UK"
    CULT_BEAUTY     = "Cult Beauty UK"
    
    # CA Retailers
    AMAZON_CA       = "Amazon CA"
    SHOPPERS_CA     = "Shoppers Drug Mart"
    SEPHORA_CA      = "Sephora Canada"
    KIYOKO_BEAUTY   = "Kiyoko Beauty CA"
    TYPEBEA_CA      = "Typebea CA"
    
    # Social Commerce & Community Discovery
    TIKTOK_SHOP     = "TikTok Shop & BeautyTok"
    REDDIT_BEAUTY   = "Reddit Beauty (r/Sephora & r/AsianBeauty)"
    QUORA_BEAUTY    = "Quora Beauty Intel"
    PINTEREST       = "Pinterest Trends"
    MANUAL          = "Manual Intel"


class GeoTarget(str, Enum):
    US = "US"
    UK = "UK"
    CA = "CA"
    GLOBAL = "GLOBAL"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TrendingProduct:
    """
    Represents a high-velocity trending beauty product discovered by the subagent.
    """
    product_name: str
    brand: str
    category: str
    trend_score: int = 0
    source_platform: str = PlatformSource.AMAZON_US.value
    geo_target: str = GeoTarget.US.value
    affiliate_url: Optional[str] = None
    price_usd: float = 0.0
    target_board: str = "Amazon Beauty Finds"
    dupe_target_brand: Optional[str] = None
    status: str = "Queued"  # Queued -> Processing -> Pinned -> Skipped
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> TrendingProduct:
        row_dict = dict(row)
        return cls(
            id=row_dict.get("id"),
            product_name=row_dict["product_name"],
            brand=row_dict.get("brand", "Generic"),
            category=row_dict.get("category", "Beauty"),
            trend_score=row_dict.get("trend_score", 0),
            source_platform=row_dict.get("source_platform", PlatformSource.AMAZON_US.value),
            geo_target=row_dict.get("geo_target", GeoTarget.US.value),
            affiliate_url=row_dict.get("affiliate_url"),
            price_usd=row_dict.get("price_usd", 0.0),
            target_board=row_dict.get("target_board", "Amazon Beauty Finds"),
            dupe_target_brand=row_dict.get("dupe_target_brand"),
            status=row_dict.get("status", "Queued"),
            created_at=row_dict.get("created_at", _utc_now()),
            updated_at=row_dict.get("updated_at", _utc_now()),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

"""
curl_cffi Engine — TLS Chrome Impersonation & Cloudflare Bypass Scraper.
========================================================================
High-speed HTTP/2 requests with browser TLS fingerprinting to bypass anti-bot shields.
"""

from __future__ import annotations

import sys
import re
import urllib.parse
from typing import List, Optional

from ..trend_models import TrendingProduct, PlatformSource, GeoTarget
from ..scoring_engine import score_trending_product

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Attempt importing curl_cffi, provide graceful urllib fallback if not installed
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    import urllib.request
    HAS_CURL_CFFI = False


def fetch_with_curl_cffi(url: str) -> str:
    """Fetch URL HTML using TLS Chrome impersonation (bypasses Cloudflare/Akamai)."""
    if HAS_CURL_CFFI:
        try:
            response = curl_requests.get(
                url,
                impersonate="chrome120",
                headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=10,
            )
            return response.text
        except Exception as err:
            print(f"⚠️ curl_cffi fetch error for {url[:40]}: {err}")
            return ""
    else:
        # Fallback to urllib with Chrome User-Agent
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as err:
            print(f"⚠️ urllib fallback fetch error for {url[:40]}: {err}")
            return ""


def scrape_fast_beauty_api(url: str, geo: str = "US") -> List[TrendingProduct]:
    """Scrape beauty trend signals fast via curl_cffi impersonation engine."""
    html = fetch_with_curl_cffi(url)
    if not html:
        return []

    products = []
    # Extract ASIN / product matches
    asins = re.findall(r"/dp/([A-Z0-9]{10})", html)
    seen = set()
    for asin in asins:
        if asin in seen:
            continue
        seen.add(asin)
        
        domain = "amazon.co.uk" if geo == "UK" else ("amazon.ca" if geo == "CA" else "amazon.com")
        aff_url = f"https://www.{domain}/dp/{asin}?tag=savvyshop0965-20"
        
        prod = TrendingProduct(
            product_name=f"Viral Beauty Item #{asin}",
            brand="Trending Brand",
            category="Beauty",
            price_usd=19.99,
            source_platform=f"Fast API ({geo})",
            geo_target=geo,
            affiliate_url=aff_url,
        )
        products.append(score_trending_product(prod))
        if len(products) >= 10:
            break

    return products


if __name__ == "__main__":
    status = "Available (TLS Impersonation Active)" if HAS_CURL_CFFI else "Fallback Mode (urllib Active)"
    print(f"✅ curl_cffi Engine Status: {status}")

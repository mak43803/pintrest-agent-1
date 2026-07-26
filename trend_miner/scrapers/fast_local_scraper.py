"""
Fast Local Scraper — Human-Mimicking Stealth Engine.
=====================================================
Uses Playwright with anti-bot stealth scripts and randomized human delays
to scrape Amazon Movers & Shakers and Sephora without bot detection.
"""

from __future__ import annotations

import os
import sys
import re
import time
import random
import urllib.parse
from typing import List
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from ..trend_models import TrendingProduct, PlatformSource, GeoTarget
from ..scoring_engine import score_trending_product

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "savvyshop0965-20")

# Anti-Bot JS Stealth Script
STEALTH_INIT_SCRIPT = """
    // 1. Remove navigator.webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => false });

    // 2. Languages fallback
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

    // 3. Mock window.chrome
    if (!window.chrome) {
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    }
"""


def fetch_playwright_html_stealth(url: str) -> str:
    """
    Fetch DOM with human-like delays, randomized viewport, and stealth JS injection.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Add small random viewport jitter to simulate human window
            w = 1280 + random.randint(-15, 15)
            h = 800 + random.randint(-15, 15)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": w, "height": h},
                locale="en-US",
                timezone_id="America/New_York",
            )
            
            # Apply stealth anti-detection script
            context.add_init_script(STEALTH_INIT_SCRIPT)
            
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Human-like natural pause (3.0 - 5.5 seconds)
            natural_delay = random.uniform(3.0, 5.5)
            print(f" ⏳ Stealth human delay: pausing {natural_delay:.1f}s to mimic natural browsing...")
            page.wait_for_timeout(int(natural_delay * 1000))
            
            # Gentle human mouse scroll
            page.mouse.wheel(0, random.randint(300, 600))
            page.wait_for_timeout(1000)
            
            html = page.content()
            browser.close()
            return html
    except Exception as err:
        print(f"⚠️ Playwright stealth fetch error for {url[:40]}: {err}")
        return ""


def parse_amazon_beauty_cards(html: str, geo: str = "US") -> List[TrendingProduct]:
    """Parse Amazon Beauty product cards from rendered HTML."""
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    products = []
    seen_asins = set()

    links = soup.find_all("a", href=re.compile(r"/dp/([A-Z0-9]{10})"))

    for link in links:
        href = link.get("href", "")
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", href)
        if not asin_match:
            continue

        asin = asin_match.group(1)
        if asin in seen_asins:
            continue
        seen_asins.add(asin)

        title = link.get_text(strip=True)
        if not title or len(title) < 8 or title.lower() in ["ratings", "stars", "reviews"]:
            parent = link.find_parent(["div", "li"])
            if parent:
                title_node = parent.find(["span", "div"], class_=re.compile(r"title|truncate|clamp|text"))
                if title_node:
                    title = title_node.get_text(strip=True)

        if not title or len(title) < 5 or title.lower() in ["ratings", "stars", "reviews"]:
            continue

        brand = title.split()[0]
        domain = "amazon.co.uk" if geo == "UK" else ("amazon.ca" if geo == "CA" else "amazon.com")
        aff_url = f"https://www.{domain}/dp/{asin}?tag={AFFILIATE_TAG}"
        platform = PlatformSource.AMAZON_UK.value if geo == "UK" else (PlatformSource.AMAZON_CA.value if geo == "CA" else PlatformSource.AMAZON_US.value)

        product = TrendingProduct(
            product_name=title[:80],
            brand=brand,
            category="Beauty",
            price_usd=19.99,
            source_platform=platform,
            geo_target=geo,
            affiliate_url=aff_url,
            target_board="Amazon Beauty Finds",
        )
        products.append(score_trending_product(product))

        if len(products) >= 15:
            break

    return products


def scrape_live_amazon_movers() -> List[TrendingProduct]:
    """Scrape live Amazon Beauty Movers & Shakers using Stealth Playwright."""
    url = "https://www.amazon.com/gp/movers-and-shakers/beauty/"
    print(f"🤖 Stealth Playwright scraping: {url}")
    html = fetch_playwright_html_stealth(url)
    return parse_amazon_beauty_cards(html, geo="US")


if __name__ == "__main__":
    prods = scrape_live_amazon_movers()
    print(f"✅ Stealth Extracted {len(prods)} live product cards from Amazon!")

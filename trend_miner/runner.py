"""
Trend Miner Runner — Autonomous Subagent Execution Engine.
===========================================================
Coordinates multi-platform discovery across US, UK, and Canada beauty retailers,
Pinterest Trends, TikTok Shop, Reddit Beauty, Quora Intel, pytrends, PRAW, and Live Feeds
using Scrapy, Crawlee, curl_cffi, and Playwright Headless engines.

Strict Daily Rules:
    1. Daily Fresh Top 5 Selection: Selects ONLY the top 5 highest-scored virals.
    2. Zero Duplicate Guarantee: Never picks previously Pinned products.
    3. Clean Active Queue: Keeps ONLY the 5 active items in queue.
"""

from __future__ import annotations

import os
import sys
import time
import argparse
from typing import Dict, Any

from .trend_models import TrendingProduct
from .trend_db import TrendDatabaseManager
from .scrapers.amazon_scrapers import fetch_amazon_trending_products
from .scrapers.sephora_scrapers import fetch_sephora_ulta_trending_products
from .scrapers.google_pinterest_trends import fetch_pinterest_google_trends
from .scrapers.multi_retailer_scrapers import fetch_multi_retailer_products
from .scrapers.pinterest_trends_scraper import fetch_live_pinterest_trends
from .scrapers.social_community_scrapers import fetch_social_community_trends
from .scrapers.github_trend_libraries import fetch_pytrends_beauty_keywords, fetch_praw_reddit_beauty_virals
from .scrapers.public_feeds_scraper import fetch_reddit_stealth_hot_posts, fetch_tiktok_creative_center_trends
from .scrapers.fast_local_scraper import scrape_live_amazon_movers
from .scrapers.curl_cffi_engine import scrape_fast_beauty_api
from .scrapers.crawlee_engine import crawl_beauty_category_pages
from .scrapers.scrapy_spider import run_bulk_scrapy_catalog_crawl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class TrendMinerRunner:
    """
    Orchestrates the 24/7 Product Intelligence Subagent pipeline across all platforms and social channels.
    """

    def __init__(self):
        self.db = TrendDatabaseManager()

    def run_sweep(self) -> Dict[str, Any]:
        """
        Execute a single product intelligence sweep across all engines, platforms, and social channels.
        Returns summary of items discovered and inserted.
        """
        print("🔍 Starting Full Product Intelligence Sweep (All Engines + Retailers + Social + Public Feeds)...")

        discovered_count = 0
        inserted_count = 0

        # 1. Amazon Sweeps & Live Playwright Scraper
        print(" 🛒 Scraping Amazon Movers & Shakers (US / UK / CA)...")
        amazon_prods = fetch_amazon_trending_products()
        live_amazon = scrape_live_amazon_movers()
        for p in amazon_prods + live_amazon:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 2. Sephora & Ulta Sweeps
        print(" 💄 Scraping Sephora & Ulta Prestige Virals...")
        prestige_prods = fetch_sephora_ulta_trending_products()
        for p in prestige_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 3. Live Pinterest Trends Scraper (trends.pinterest.com)
        print(" 📌 Fetching Live Pinterest Trends Signals (US, UK, CA)...")
        pin_us = fetch_live_pinterest_trends("US")
        pin_uk = fetch_live_pinterest_trends("UK")
        pin_ca = fetch_live_pinterest_trends("CA")
        for p in pin_us + pin_uk + pin_ca:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 4. Public Feeds (Live Reddit Stealth Hot Feeds & TikTok Creative Center)
        print(" 🌐 Scraping Live Reddit Hot Feeds (r/AsianBeauty, r/Sephora) & TikTok Creative Center...")
        red_ab = fetch_reddit_stealth_hot_posts("AsianBeauty")
        red_sep = fetch_reddit_stealth_hot_posts("Sephora")
        tik_cc = fetch_tiktok_creative_center_trends()
        for p in red_ab + red_sep + tik_cc:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 5. Social Commerce & Community Discovery (TikTok Shop, Reddit Beauty, Quora Intel)
        print(" 🎵 Scraping TikTok Shop Virals, Reddit Beauty, and Quora Intel...")
        social_prods = fetch_social_community_trends()
        for p in social_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 6. Open-Source Trend Libraries (pytrends & PRAW)
        print(" 📈 Running pytrends Search Velocity & PRAW Reddit Community Engine...")
        py_prods = fetch_pytrends_beauty_keywords()
        pr_prods = fetch_praw_reddit_beauty_virals()
        for p in py_prods + pr_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 7. Multi-Retailer Ecosystem (US Target/CVS/Stylevana, UK Boots/SpaceNK, CA Shoppers/Kiyoko/Typebea)
        print(" 🌐 Scraping US, UK & CA Major Retailers...")
        multi_prods = fetch_multi_retailer_products()
        for p in multi_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 8. curl_cffi Fast TLS Impersonation Engine
        print(" ⚡ Running curl_cffi Fast Anti-Bot Impersonation Engine...")
        cffi_prods = scrape_fast_beauty_api("https://www.amazon.com/gp/movers-and-shakers/beauty/", geo="US")
        for p in cffi_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 9. Crawlee Smart Session & Pagination Engine
        print(" 🕷️ Running Crawlee Multi-Page Session Crawler...")
        crawlee_prods = crawl_beauty_category_pages("https://www.sephora.com/shop/bestselling-beauty-products", geo="US")
        for p in crawlee_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # 10. Scrapy Bulk Catalog Spider
        print(" 🚀 Running Scrapy Bulk Catalog Spider...")
        scrapy_prods = run_bulk_scrapy_catalog_crawl("Amazon US")
        for p in scrapy_prods:
            discovered_count += 1
            res = self.db.add_product(p)
            if res is not None:
                inserted_count += 1

        # Extract & activate ONLY the top 5 fresh daily virals
        top5 = self.db.get_fresh_daily_top_5_virals()

        stats = self.db.get_stats()
        print("\n" + "═" * 65)
        print(" 🎉 FULL DISCOVERY SWEEP COMPLETE (DAILY TOP 5 ACTIVATED)")
        print("═" * 65)
        print(f" 📥 Total Products Evaluated : {discovered_count}")
        print(f" ✨ New Items Added to Pool  : {inserted_count}")
        print(f" 📦 Total Pool Size in DB    : {stats['total_products']}")
        print(f" 🔥 Active Daily Top 5 Virals: {len(top5)} items")
        print(f" 📜 Pinned Products History  : {stats['pinned_history']} items")
        print("═" * 65 + "\n")

        return {
            "evaluated": discovered_count,
            "inserted": inserted_count,
            "top5": [p.to_dict() for p in top5],
            "stats": stats,
        }

    def print_top5(self) -> None:
        """Print the ABSOLUTE TOP 5 DAILY VIRAL PRODUCTS for immediate pin creation."""
        top5 = self.db.get_fresh_daily_top_5_virals()

        print("\n" + "═" * 65)
        print(" 🔥 FRESH DAILY TOP 5 VIRAL BEAUTY PRODUCTS (STRICT UNPINNED QUEUE)")
        print("═" * 65)
        for idx, p in enumerate(top5, start=1):
            print(f" 🥇 Rank #{idx}: [{p.geo_target} | {p.source_platform}] {p.brand} - {p.product_name}")
            print(f"    Category: {p.category} | Board: {p.target_board} | PIS Score: {p.trend_score}/40")
            print(f"    Status: {p.status} | Affiliate Link: {p.affiliate_url}")
            print("─" * 65)
        print("═" * 65 + "\n")

    def print_report(self) -> None:
        """Print detailed summary report of product pool."""
        stats = self.db.get_stats()
        top5 = self.db.get_fresh_daily_top_5_virals()

        print("\n" + "═" * 65)
        print(" 👑 TREND MINER AGENT — GLOBAL BEAUTY POOL REPORT")
        print("═" * 65)
        print(f" 📦 Total Pool Size    : {stats['total_products']}")
        print(f" 🔥 Active Daily Top 5 : {stats['active_daily_top5']}")
        print(f" 📌 Pinned History     : {stats['pinned_history']} items")
        print(f" 🌟 Unpinned Priority  : {stats['unpinned_high_priority_30plus']} items (PIS ≥ 30)")
        print("─" * 65)
        print(" 🔥 ACTIVE DAILY TOP 5 VIRALS QUEUE:")
        for idx, p in enumerate(top5, start=1):
            print(f"   {idx:2d}. [{p.geo_target} | {p.source_platform}] {p.brand} - {p.product_name}")
            print(f"       Category: {p.category} | Board: {p.target_board} | PIS: {p.trend_score}/40")
        print("═" * 65 + "\n")

    def run_daemon(self, interval_seconds: int = 21600) -> None:
        """
        Run 24/7 background loop performing discovery sweeps every interval.
        Default: 6 hours (21600s).
        """
        print(f"🤖 Starting 24/7 Product Intelligence Daemon (Sweep Interval: {interval_seconds // 3600}h)...")
        try:
            while True:
                self.run_sweep()
                print(f"😴 Daemon sleeping for {interval_seconds} seconds. Waiting for next sweep...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Daemon stopped by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Product Intelligence & Trend Miner Agent")
    parser.add_argument("--run-once", action="store_true", help="Run a single product discovery sweep")
    parser.add_argument("--top5", action="store_true", help="Print the absolute Top 5 Daily Virals for pin priority")
    parser.add_argument("--daemon", action="store_true", help="Run 24/7 background intelligence daemon")
    parser.add_argument("--report", action="store_true", help="Print summary report of product pool")
    parser.add_argument("--interval", type=int, default=21600, help="Daemon sleep interval in seconds (default 6h)")

    args = parser.parse_args()
    runner = TrendMinerRunner()

    if args.top5:
        runner.print_top5()
    elif args.daemon:
        runner.run_daemon(interval_seconds=args.interval)
    elif args.report:
        runner.print_report()
    else:
        runner.run_sweep()
        runner.print_top5()

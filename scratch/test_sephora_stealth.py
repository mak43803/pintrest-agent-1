"""
Test Sephora Stealth Scraping using Crawl4AI
"""
import asyncio
import sys
from crawl4ai import AsyncWebCrawler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_sephora_crawl4ai():
    url = "https://www.sephora.com/shop/makeup-cosmetics"
    print(f"🚀 Testing Crawl4AI on Sephora: {url}...")

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)
        print(f"✅ Crawl Completed! Success: {result.success}")
        print(f"📌 Markdown Content length: {len(result.markdown or '')}")
        print(f"📸 Images: {len(result.media.get('images', [])) if result.media else 0}")
        
        snippet = (result.markdown or "")[:600]
        print("\n--- Sephora Content Snippet ---")
        print(snippet)

if __name__ == "__main__":
    asyncio.run(test_sephora_crawl4ai())

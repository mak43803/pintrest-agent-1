"""
Demo: E-commerce Product Extraction using Crawl4AI
"""
import asyncio
import sys
from crawl4ai import AsyncWebCrawler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_crawl(url: str):
    print(f"🚀 Initializing Crawl4AI Web Crawler for URL: {url}...")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)
        print("✅ Crawl Completed!")
        print("📌 Markdown Content length:", len(result.markdown or ""))
        print("📸 Media/Images extracted:", len(result.media.get("images", [])) if result.media else 0)
        
        # Display sample snippet
        snippet = (result.markdown or "")[:400]
        print("\n--- Product Content Snippet ---")
        print(snippet)

if __name__ == "__main__":
    target_url = "https://www.amazon.com/dp/B08R994Q1L"
    asyncio.run(test_crawl(target_url))

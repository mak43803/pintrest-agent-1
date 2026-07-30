"""
Test Sephora Category Extraction using Playwright Stealth / Crawl4AI
"""
import asyncio
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEPHORA_CATEGORIES = {
    "New": "https://www.sephora.com/shop/new-beauty-products",
    "Makeup": "https://www.sephora.com/shop/makeup-cosmetics",
    "Skincare": "https://www.sephora.com/shop/skincare",
    "Fragrance": "https://www.sephora.com/shop/fragrance",
    "Hair": "https://www.sephora.com/shop/hair-care",
    "Bath & Body": "https://www.sephora.com/shop/bath-body",
    "Mini Size": "https://www.sephora.com/shop/travel-size-toiletries-beauty-products",
    "Gifts & Value Sets": "https://www.sephora.com/shop/gift"
}

async def test_sephora_category(cat_name, url):
    print(f"🌐 Testing Sephora Category: {cat_name} -> {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

            for _ in range(6):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(600)

            product_links = page.locator("a[href*='/product/']")
            count = await product_links.count()
            print(f"   📦 [{cat_name}] Found /product/ links: {count}")

            seen = set()
            for i in range(min(count, 5)):
                link = product_links.nth(i)
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip().replace("\n", " ")
                if href and href not in seen:
                    seen.add(href)
                    print(f"      • Product #{i+1}: {text[:50]} | URL: {href[:50]}")

        except Exception as e:
            print(f"   ❌ [{cat_name}] Error: {e}")

        finally:
            await browser.close()

async def main():
    for name, url in list(SEPHORA_CATEGORIES.items())[:3]:
        await test_sephora_category(name, url)

if __name__ == "__main__":
    asyncio.run(main())

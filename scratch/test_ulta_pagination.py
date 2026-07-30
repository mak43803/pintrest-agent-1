"""
Test Ulta Pagination Crawling (Pages 1 to 5)
"""
import asyncio
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        total_extracted = 0
        seen_urls = set()

        for page_num in range(1, 6):
            url = f"https://www.ulta.com/shop/all?minAmount=0&maxAmount=20&page={page_num}"
            print(f"📄 Scraping Page {page_num}: {url}...")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                for _ in range(6):
                    await page.mouse.wheel(0, 1000)
                    await page.wait_for_timeout(600)

                product_links = page.locator("a[href*='/p/']")
                count = await product_links.count()
                
                page_items = 0
                for i in range(count):
                    href = await product_links.nth(i).get_attribute("href") or ""
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        page_items += 1

                total_extracted += page_items
                print(f"   ✅ Page {page_num} Yield: {page_items} unique items (Total so far: {total_extracted})")

            except Exception as e:
                print(f"   ❌ Page {page_num} Error: {e}")

        await browser.close()
        print(f"🎉 Total Unique Ulta Products Found Across 5 Pages: {total_extracted}")

if __name__ == "__main__":
    asyncio.run(main())

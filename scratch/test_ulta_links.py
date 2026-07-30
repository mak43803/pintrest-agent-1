"""
Ulta Beauty Links Deep Inspection Script
"""
import asyncio
import sys
import re
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    url = "https://www.ulta.com/shop/all?minAmount=0&maxAmount=20"
    print(f"🌐 Opening Ulta Beauty: {url}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

            for _ in range(8):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(800)

            # Locate all product links
            product_links = page.locator("a[href*='/p/']")
            count = await product_links.count()
            print(f"🔗 Total /p/ product links found: {count}")

            extracted_items = []
            seen_urls = set()

            for i in range(count):
                link = product_links.nth(i)
                href = await link.get_attribute("href") or ""
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                text = (await link.inner_text()).strip()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                full_url = href if href.startswith("http") else f"https://www.ulta.com{href}"
                clean_name = " ".join(lines)
                
                # Check parent container for image and price
                parent = link.locator("xpath=..")
                img_loc = parent.locator("img").first
                img_src = ""
                if await img_loc.count() > 0:
                    img_src = await img_loc.get_attribute("src") or await img_loc.get_attribute("data-src") or ""

                extracted_items.append({
                    "title": clean_name,
                    "url": full_url,
                    "img": img_src
                })

            print(f"✅ Unique items extracted: {len(extracted_items)}")
            for idx, item in enumerate(extracted_items[:10], start=1):
                print(f" [{idx:02d}] {item['title'][:60]} | URL: {item['url'][:50]}")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

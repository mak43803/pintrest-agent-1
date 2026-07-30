"""
Inspect Sephora DOM for product links & JSON-LD
"""
import asyncio
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    url = "https://www.sephora.com/shop/makeup-cosmetics"
    print(f"🌐 Inspecting Sephora DOM: {url}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            for _ in range(6):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(800)

            title = await page.title()
            print(f"📄 Page Title: {title}")

            # Inspect all <a> tags
            all_links = page.locator("a")
            count = await all_links.count()
            print(f"🔗 Total <a> links on Sephora page: {count}")

            product_candidates = []
            for i in range(min(count, 150)):
                link = all_links.nth(i)
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip().replace("\n", " ")
                if any(p in href for p in ["-P", "/product/", "P", "sku"]):
                    if text and len(text) > 3 and "sign in" not in text.lower():
                        product_candidates.append((text, href))

            print(f"📦 Product Link Candidates Found: {len(product_candidates)}")
            for idx, (t, h) in enumerate(product_candidates[:10], start=1):
                print(f"   [{idx:02d}] {t[:50]} | URL: {h[:50]}")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

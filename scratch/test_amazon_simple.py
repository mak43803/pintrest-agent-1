"""
Test Amazon Search without category param
"""
import asyncio
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    q = "Sephora viral beauty products"
    url = f"https://www.amazon.com/s?k={q.replace(' ', '+')}"
    print(f"🌐 Testing Amazon Search: {url}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            cards = page.locator('div[data-component-type="s-search-result"]')
            count = await cards.count()
            print(f"📦 Total Search Cards Found: {count}")

            links = page.locator("a[href*='/dp/']")
            link_count = await links.count()
            print(f"🔗 Total /dp/ links found: {link_count}")

            for i in range(min(link_count, 5)):
                href = await links.nth(i).get_attribute("href") or ""
                text = (await links.nth(i).inner_text()).strip().replace("\n", " ")
                print(f"   • Link #{i+1}: {text[:40]} | {href[:50]}")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

"""
Test Amazon Search via BrowserManager persistent profile
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))

from browser.browser_manager import BrowserManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    q = "Sephora viral makeup products"
    bm = BrowserManager()
    await bm.initialize()

    context = bm.context
    page = await context.new_page()

    try:
        url = f"https://www.amazon.com/s?k={q.replace(' ', '+')}&i=beauty"
        print(f"🌐 Navigating to Amazon Search with persistent session: {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        result_cards = page.locator('div[data-component-type="s-search-result"]')
        count = await result_cards.count()
        print(f"📦 Total Search Result Cards Found: {count}")

        for i in range(min(count, 5)):
            card = result_cards.nth(i)
            link_loc = card.locator('a[href*="/dp/"]').first
            if await link_loc.count() > 0:
                href = await link_loc.get_attribute("href") or ""
                text = (await link_loc.inner_text()).strip().replace("\n", " ")
                print(f"   • Item #{i+1}: {text[:50]} | {href[:50]}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await page.close()
        await bm.close()

if __name__ == "__main__":
    asyncio.run(main())

"""
Test Card Title & Link Extraction from Amazon Search Cards
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from browser.browser_manager import BrowserManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    bm = BrowserManager()
    await bm.initialize()
    page = await bm.context.new_page()

    try:
        url = "https://www.amazon.com/s?k=Sephora+liquid+blush+soft+pinch"
        print(f"🌐 Navigating: {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        cards = page.locator('div[data-component-type="s-search-result"]')
        count = await cards.count()
        print(f"📦 Total Search Cards Found: {count}")

        extracted = []
        for i in range(min(count, 15)):
            card = cards.nth(i)
            link_loc = card.locator('a[href*="/dp/"]').first
            if await link_loc.count() == 0:
                continue

            href = await link_loc.get_attribute("href") or ""
            
            # Title is in h2 or span.a-text-normal
            title_loc = card.locator('h2, span.a-text-normal, a.a-text-normal').first
            title_text = ""
            if await title_loc.count() > 0:
                title_text = (await title_loc.inner_text()).strip().replace("\n", " ")

            if not title_text:
                title_text = (await card.inner_text()).split("\n")[0].strip()

            if title_text and "/dp/" in href:
                extracted.append((title_text, href))

        print(f"✅ Successfully Extracted {len(extracted)} Clean Items!")
        for idx, (t, h) in enumerate(extracted[:5], start=1):
            print(f"   [{idx:02d}] {t[:60]} | URL: {h[:50]}")

    finally:
        await page.close()
        await bm.close()

if __name__ == "__main__":
    asyncio.run(main())

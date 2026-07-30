"""
Test Multi-Tab Amazon Category Mining
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from browser.browser_manager import BrowserManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_single_vector(q):
    bm = BrowserManager()
    await bm.initialize()
    page = await bm.context.new_page()

    try:
        url = f"https://www.amazon.com/s?k={q.replace(' ', '+')}"
        print(f"🌐 Querying: {q} -> {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2500)

        cards = page.locator('div[data-component-type="s-search-result"]')
        count = await cards.count()
        print(f"📦 Cards Found: {count}")

        items = []
        for i in range(min(count, 10)):
            card = cards.nth(i)
            link_loc = card.locator('a[href*="/dp/"]').first
            if await link_loc.count() > 0:
                href = await link_loc.get_attribute("href") or ""
                text = (await link_loc.inner_text()).strip().replace("\n", " ")
                if len(text) > 5:
                    items.append((text, href))

        print(f"   ✅ Clean Items Extracted: {len(items)}")
        for idx, (t, h) in enumerate(items[:3], start=1):
            print(f"      [{idx}] {t[:45]} | {h[:45]}")

    finally:
        await page.close()
        await bm.close()

if __name__ == "__main__":
    asyncio.run(test_single_vector("Sephora liquid blush soft pinch"))

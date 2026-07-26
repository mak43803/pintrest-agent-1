import asyncio
from browser.browser_manager import BrowserManager
from playwright.async_api import Page
import time

async def test_trends():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    try:
        print("Navigating to Pinterest Trends (Beauty)...")
        # Try finding beauty category
        await page.goto("https://trends.pinterest.com/?country=US", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # See if there's a filter for category
        print("Looking for category dropdown...")
        dropdowns = await page.locator('div[role="combobox"]').all()
        for d in dropdowns:
            print(f"Dropdown: {await d.inner_text()}")
            
        print("Dumping all text...")
        texts = await page.locator('span, div, h2, h3, a').all_inner_texts()
        valid_texts = set()
        for t in texts:
            if t.strip() and len(t.strip()) > 3 and len(t.strip()) < 50:
                valid_texts.add(t.strip())
                
        for t in list(valid_texts)[:50]:
            print(t)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test_trends())

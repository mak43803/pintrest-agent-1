import asyncio
from browser.browser_manager import BrowserManager

async def test_google_trends():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    try:
        # Category 44 is "Beauty & Fitness" in Google Trends
        # Alternatively, Google daily trends URL: https://trends.google.com/trending?geo=US
        print("Navigating to Google Trends (US)...")
        await page.goto("https://trends.google.com/trending?geo=US", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        print("Dumping all text...")
        texts = await page.locator('div, span, a').all_inner_texts()
        valid_texts = set()
        for t in texts:
            if t.strip() and 4 < len(t.strip()) < 40 and "K" not in t and "+" not in t:
                valid_texts.add(t.strip())
                
        for t in list(valid_texts)[:30]:
            print(t)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test_google_trends())

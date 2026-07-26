import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    
    try:
        page = manager.context.pages[0]
        
        # Step 1: Go to admin home first
        print("Going to admin home...")
        await page.goto("https://linktr.ee/admin", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        print(f"URL after admin: {page.url}")
        body = await page.locator("body").inner_text()
        print(f"Body length: {len(body)}")
        print(f"Body excerpt: {body[:200]}")
        
        # Step 2: Click the 'Shop' link in sidebar
        print("\nClicking Shop in sidebar...")
        shop_link = page.get_by_role("link", name="Shop").first
        if await shop_link.is_visible():
            await shop_link.click()
            await page.wait_for_timeout(5000)
        else:
            print("Shop link not visible, trying direct URL...")
            await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
            await page.wait_for_timeout(8000)
        
        print(f"\nURL after shop click: {page.url}")
        
        # Step 3: Look for category
        category = "Gamer Tech (Test)"
        body2 = await page.locator("body").inner_text()
        print(f"Body2 length: {len(body2)}")
        if category in body2:
            print("FOUND in body!")
        else:
            print("NOT FOUND in body")
            print(f"Body excerpt: {body2[:500]}")
            
        # Screenshot
        await page.screenshot(path=r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\shop_after_nav.png", full_page=True)
        print("Screenshot saved.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = manager.context.pages[0]
    
    print("Navigating to Linktree Admin...")
    await page.goto("https://linktr.ee/admin", wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    
    print("Clicking Shop sidebar link...")
    shop_link = page.locator('a[href*="/admin/shop"], a:has-text("Shop"), button:has-text("Shop")').filter(visible=True).first
    if await shop_link.count() > 0:
        await shop_link.click(force=True)
        await page.wait_for_timeout(5000)
        
    await page.screenshot(path="debug_tab_manage.png", full_page=True)
    print("Saved debug_tab_manage.png")
    
    # Check text on Manage screen
    txt1 = await page.evaluate("() => (document.querySelector('main') || document.body).innerText")
    print(f"Manage tab text ({len(txt1)} chars):\n{txt1[:300]}")
    
    # Find Affiliate Products tab and click it
    aff_tab = page.locator('button:has-text("Affiliate Products"), a:has-text("Affiliate Products"), *:has-text("Affiliate Products")').filter(visible=True).first
    if await aff_tab.count() > 0:
        print("\nClicking 'Affiliate Products' tab...")
        await aff_tab.click(force=True)
        await page.wait_for_timeout(5000)
        await page.screenshot(path="debug_tab_affiliate.png", full_page=True)
        print("Saved debug_tab_affiliate.png")
        
        txt2 = await page.evaluate("() => (document.querySelector('main') || document.body).innerText")
        print(f"Affiliate Products tab text ({len(txt2)} chars):\n{txt2[:300]}")
    else:
        print("Could not find 'Affiliate Products' tab!")

    # Check all buttons on active page
    btns = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('button, a, [role="button"]')).map(el => {
            const r = el.getBoundingClientRect();
            const txt = (el.innerText || el.textContent || '').trim();
            if (r.width > 0 && r.height > 0 && txt.length > 0 && txt.length < 80) {
                return { tag: el.tagName, txt: txt, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
            }
            return null;
        }).filter(Boolean);
    }''')
    
    print(f"\nAll visible buttons on page ({len(btns)}):")
    for b in btns:
        print(f"  [{b['tag']}] x={b['x']}, y={b['y']}, w={b['w']}, h={b['h']} | '{b['txt']}'")
        
    await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

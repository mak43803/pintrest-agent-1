import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = manager.context.pages[0]
    
    print("1. Navigating to main admin page: https://linktr.ee/admin...")
    await page.goto("https://linktr.ee/admin", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    
    print("2. Clicking 'Shop' link in sidebar...")
    shop_link = page.locator('a[href*="/admin/shop"], a:has-text("Shop"), button:has-text("Shop")').filter(visible=True).first
    if await shop_link.count() > 0:
        await shop_link.click(force=True)
        print("Click successful! Waiting 5s for SPA navigation...")
        await page.wait_for_timeout(5000)
    else:
        print("Could not find visible Shop link in sidebar! Trying direct click...")
        await page.click('text="Shop"')
        await page.wait_for_timeout(5000)
        
    print(f"Current URL: {page.url}")
    await page.screenshot(path="spa_shop_screenshot.png", full_page=True)
    print("Saved spa_shop_screenshot.png")
    
    # Check for buttons or text
    btns = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('button, a, div')).map(el => {
            const r = el.getBoundingClientRect();
            const t = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
            if (r.width > 50 && r.height > 15 && (t.includes('Add') || t.includes('Collection') || t.includes('Product'))) {
                return { tag: el.tagName, txt: t, bbox: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
            }
            return null;
        }).filter(Boolean);
    }''')
    
    print(f"\nFound {len(btns)} interactive buttons/cards:")
    for b in btns[:15]:
        print(f"  [{b['tag']}] bbox={b['bbox']} | txt='{b['txt'][:60]}'")
        
    await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

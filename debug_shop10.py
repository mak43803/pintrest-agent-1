import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(5000)
    
    print("Clicking main Add button...")
    add_btn = page.get_by_role('button', name='Add', exact=True).first
    if await add_btn.is_visible():
        await add_btn.click(force=True)
        
    await page.wait_for_timeout(3000)
    
    print("Clicking Linked product...")
    linked = page.locator('button:has-text("Linked product")').first
    if await linked.is_visible():
        await linked.click(force=True)
        await page.wait_for_timeout(2000)
        
    search = page.locator('input[placeholder*="Search products"]').first
    await search.fill('https://www.amazon.com/dp/B0BGN816K8')
    await page.wait_for_timeout(5000)
    
    print("Clicking Amazon result...")
    for btn in await page.locator('button').all():
        try:
            txt = (await btn.inner_text()).strip()
            if 'amazon' in txt.lower() and len(txt) > 20:
                await btn.click(force=True)
                break
        except Exception:
            pass
            
    await page.wait_for_timeout(5000)
    
    print("Taking screenshot of the final modal!")
    await page.screenshot(path="final_shop_modal.png", full_page=True)
    
    await m.close()
    
asyncio.run(main())

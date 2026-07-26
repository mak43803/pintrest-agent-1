import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    print("Waiting for page load...")
    for attempt in range(10):
        await page.wait_for_timeout(3000)
        btn = page.locator('button:has-text("Edit")').first
        if await btn.is_visible():
            print('Shop loaded!')
            break
            
    print("Clicking Add button...")
    add_btn = page.locator('button:has-text("Add")').first
    await add_btn.wait_for(state='visible')
    await add_btn.click(force=True)
    
    await page.wait_for_timeout(3000)
    await page.screenshot(path='linktree_shop_debug_add_modal.png')
    
    print("Clicking Linked product...")
    linked_btn = page.locator('button:has-text("Linked product")').first
    if await linked_btn.is_visible():
        await linked_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
        search_input = page.locator('input[placeholder*="Search products"]').first
        await search_input.fill('https://www.amazon.com/dp/B0BGN816K8')
        await page.wait_for_timeout(5000)
        await page.screenshot(path='linktree_shop_debug_search.png')
        
        print("Clicking amazon result...")
        for btn in await page.locator('button').all():
            try:
                txt = (await btn.inner_text()).strip()
                if 'amazon' in txt.lower() and len(txt) > 20:
                    await btn.click(force=True)
                    break
            except Exception:
                pass
                
        await page.wait_for_timeout(3000)
        await page.screenshot(path='linktree_shop_debug_after_click.png')
    else:
        print("Linked product button not visible!")
        
    await m.close()
    
asyncio.run(main())

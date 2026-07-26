import asyncio
from browser.browser_manager import BrowserManager
async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    # Wait for Edit button to show up
    for attempt in range(10):
        await page.wait_for_timeout(3000)
        try:
            btn = page.locator('button:has-text("Edit")').first
            if await btn.is_visible():
                print('Shop loaded!')
                break
        except Exception:
            pass
            
    # Click Add
    add_btn = page.locator('button:has-text("Add")').first
    if await add_btn.is_visible():
        await add_btn.click(force=True)
        await page.wait_for_timeout(2000)
        
        # Click Linked product
        linked_btn = page.locator('button:has-text("Linked product")').first
        if await linked_btn.is_visible():
            await linked_btn.click(force=True)
            await page.wait_for_timeout(3000)
            
            # Fill URL
            search_input = page.locator('input[placeholder*="Search products"]').first
            await search_input.fill('https://www.amazon.com/dp/B0BGN816K8')
            await page.wait_for_timeout(5000)
            
            await page.screenshot(path='linktree_shop_debug3_search_results.png')
            
            # Click Amazon result
            for btn in await page.locator('button').all():
                try:
                    txt = (await btn.inner_text()).strip()
                    if 'amazon' in txt.lower() and len(txt) > 20:
                        await btn.click(force=True)
                        break
                except Exception:
                    pass
                    
            await page.wait_for_timeout(4000)
            await page.screenshot(path='linktree_shop_debug4_after_click.png')
            
    await m.close()
asyncio.run(main())

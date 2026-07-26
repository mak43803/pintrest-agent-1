import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    print('Switching to Affiliate Products tab...')
    await page.wait_for_timeout(5000)
    
    # Click 'Affiliate Products' tab
    tab_btn = page.locator('text="Affiliate Products"').first
    await tab_btn.click(force=True)
    await page.wait_for_timeout(4000)
    await page.screenshot(path='linktree_debug_after_tab.png')
    
    print('Clicking Add button in Affiliate Products...')
    # Look for button that exactly says Add or + Add
    add_btn = page.locator('button:has-text("Add")')
    for i in range(await add_btn.count()):
        btn = add_btn.nth(i)
        if await btn.is_visible():
            txt = await btn.inner_text()
            if txt.strip() == "Add" or "+ Add" in txt:
                print(f"Clicking visible Add button with text: {txt}")
                await btn.click(force=True)
                break
                
    await page.wait_for_timeout(3000)
    await page.screenshot(path='linktree_shop_debug_affiliate_add.png')
    
    print('Clicking Linked product...')
    linked_btn = page.locator('button:has-text("Linked product")').first
    if await linked_btn.is_visible():
        await linked_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
        search_input = page.locator('input[placeholder*="Search products"]').first
        await search_input.fill('https://www.amazon.com/dp/B0BGN816K8')
        await page.wait_for_timeout(5000)
        
        print('Clicking amazon result...')
        for btn in await page.locator('button').all():
            try:
                txt = (await btn.inner_text()).strip()
                if 'amazon' in txt.lower() and len(txt) > 20:
                    await btn.click(force=True)
                    break
            except Exception:
                pass
                
        await page.wait_for_timeout(3000)
        await page.screenshot(path='linktree_shop_debug_affiliate_after_click.png')
    else:
        print("Linked product button not visible!")
        
    await m.close()
    
asyncio.run(main())

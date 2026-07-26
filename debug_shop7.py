import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(5000)
    
    # Click 'Affiliate Products' tab
    tab_btn = page.locator('button', has_text='Affiliate Products').first
    if await tab_btn.is_visible():
        await tab_btn.click(force=True)
    else:
        # Sometimes it's not a button
        await page.locator('text="Affiliate Products"').first.click(force=True)
        
    await page.wait_for_timeout(3000)
    
    print('Clicking exact Add button...')
    # Match button with exact accessible name "Add"
    add_btn = page.get_by_role('button', name='Add', exact=True).first
    if await add_btn.is_visible():
        await add_btn.click(force=True)
    else:
        print("Could not find Add button!")
        return
        
    await page.wait_for_timeout(3000)
    
    print('Checking if we need to click Linked product...')
    # When clicking Add on the affiliate tab, it might jump straight to the search modal!
    linked_btn = page.locator('button:has-text("Linked product")').first
    if await linked_btn.is_visible():
        await linked_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
    # Now we should be at the search modal
    search_input = page.locator('input[placeholder*="Search products"]').first
    if await search_input.is_visible():
        await search_input.fill('https://www.amazon.com/dp/B0BGN816K8')
        await page.wait_for_timeout(5000)
        
        print('Clicking amazon result...')
        clicked = False
        for btn in await page.locator('button').all():
            try:
                txt = (await btn.inner_text()).strip()
                if 'amazon' in txt.lower() and len(txt) > 20:
                    await btn.click(force=True)
                    clicked = True
                    break
            except Exception:
                pass
                
        if clicked:
            print('Clicked result! Waiting to see what appears...')
            await page.wait_for_timeout(3000)
            await page.screenshot(path='linktree_final_debug.png')
            
            btns = await page.locator('button').all_inner_texts()
            print('Visible buttons:', [b for b in btns if b.strip()])
        else:
            print('Amazon result not found')
            
    await m.close()
    
asyncio.run(main())

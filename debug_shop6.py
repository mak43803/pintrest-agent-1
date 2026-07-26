import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(5000)
    print('Clicking Add button in Manage tab...')
    # Use exact match or look for + Add
    add_btn = page.locator('button:has-text("+ Add")').first
    if await add_btn.is_visible():
        print(f"Found + Add button")
        await add_btn.click(force=True)
                
    await page.wait_for_timeout(3000)
    
    linked_btn = page.locator('button:has-text("Linked product")').first
    if await linked_btn.is_visible():
        print('Clicking Linked product...')
        await linked_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
        search_input = page.locator('input[placeholder*="Search products"]').first
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
            print('Clicked amazon result. Waiting to see if we need to click Add to shop or Save...')
            await page.wait_for_timeout(3000)
            await page.screenshot(path='linktree_after_amazon_result_manage.png')
            
            btns = await page.locator('button').all_inner_texts()
            print('Visible buttons:', [b for b in btns if b.strip()])
        else:
            print('Could not find amazon result button')
    else:
        print("Linked product button not found")
        
    await m.close()
    
asyncio.run(main())

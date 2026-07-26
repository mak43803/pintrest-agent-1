"""
Debug: Explore Linktree SHOP section — find the correct flow for adding affiliate products.
User flow: Shop → Add (+) → "Add a link product to your shop" → paste link → done
Also: Collections for grouping (30 per group)
"""
import asyncio
import sys
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")

PROJECT_ROOT = Path(__file__).parent
USER_DATA_DIR = str(PROJECT_ROOT / "browser_session")

async def main():
    print("🔍 Exploring Linktree SHOP section...")
    
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False,
        viewport={"width": 1280, "height": 800},
        slow_mo=100,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ]
    )
    
    page = await context.new_page()
    
    # Try different shop URLs
    shop_urls = [
        "https://linktr.ee/admin/shop",
        "https://linktr.ee/admin/commerce",
        "https://linktr.ee/admin/store",
        "https://linktr.ee/admin/products",
    ]
    
    # First go to admin to check login
    await page.goto("https://linktr.ee/admin", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    
    if "login" in page.url.lower():
        print("❌ Not logged in!")
        await context.close()
        await pw.stop()
        return
    
    print("✅ Logged in!")
    
    # Look for Shop/Store navigation link in sidebar
    print("\n📌 Step 1: Finding Shop navigation...")
    nav_links = await page.locator('a, button').all()
    for i, link in enumerate(nav_links):
        try:
            visible = await link.is_visible()
            if not visible:
                continue
            text = (await link.inner_text()).strip().replace('\n', ' ')[:80]
            href = await link.get_attribute("href") or ""
            if any(word in text.lower() for word in ["shop", "store", "commerce", "product", "sell"]):
                print(f"   ✅ Nav [{i}]: text='{text}' | href='{href}'")
        except:
            pass
    
    # Try going to shop URL directly
    print("\n📌 Step 2: Trying shop URLs...")
    for url in shop_urls:
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            final_url = page.url
            title = await page.title()
            print(f"   {url} → landed on: {final_url} | title: {title}")
            
            if final_url != "https://linktr.ee/admin" and "login" not in final_url:
                # This URL worked! Let's explore
                print(f"   ✅ Found shop at: {final_url}")
                break
        except:
            pass
    
    # Screenshot current page
    await page.screenshot(path=str(PROJECT_ROOT / "linktree_shop.png"))
    print(f"\n📸 Screenshot: linktree_shop.png")
    print(f"📌 Current URL: {page.url}")
    
    # Find ALL buttons and interactive elements on the shop page
    print("\n📌 Step 3: All visible buttons on shop page...")
    buttons = await page.locator("button, a[role='button']").all()
    for i, btn in enumerate(buttons):
        try:
            visible = await btn.is_visible()
            if not visible:
                continue
            text = (await btn.inner_text()).strip().replace('\n', ' ')[:80]
            href = await btn.get_attribute("href") or ""
            testid = await btn.get_attribute("data-testid") or ""
            aria = await btn.get_attribute("aria-label") or ""
            if text or testid or aria:
                print(f"   Button [{i}]: text='{text}' | testid='{testid}' | aria='{aria}' | href='{href}'")
        except:
            pass
    
    # Find ALL links on the page
    print("\n📌 Step 4: All navigation links...")
    links = await page.locator("a").all()
    for i, link in enumerate(links):
        try:
            visible = await link.is_visible()
            if not visible:
                continue
            text = (await link.inner_text()).strip().replace('\n', ' ')[:60]
            href = await link.get_attribute("href") or ""
            if text and href:
                print(f"   Link [{i}]: text='{text}' | href='{href}'")
        except:
            pass
    
    # Look for Add/Plus button specifically  
    print("\n📌 Step 5: Looking for Add/Plus button...")
    add_selectors = [
        'button[aria-label*="Add"]',
        'button[aria-label*="add"]',
        'button:has-text("Add")',
        'button:has-text("+")',
        '[data-testid*="add"]',
        '[data-testid*="Add"]',
        'a:has-text("Add")',
        'button:has-text("New")',
        'button:has-text("Create")',
    ]
    for sel in add_selectors:
        try:
            items = await page.locator(sel).all()
            for item in items:
                visible = await item.is_visible()
                if visible:
                    text = (await item.inner_text()).strip().replace('\n', ' ')[:60]
                    testid = await item.get_attribute("data-testid") or ""
                    aria = await item.get_attribute("aria-label") or ""
                    print(f"   ✅ {sel}: text='{text}' | testid='{testid}' | aria='{aria}'")
        except:
            pass
    
    # Look for "Add a link product" text
    print("\n📌 Step 6: Looking for 'Add a link product' or similar text...")
    product_selectors = [
        '*:has-text("Add a link product")',
        '*:has-text("link product")',
        '*:has-text("Add product")',
        '*:has-text("add product")',
        'button:has-text("product")',
        'a:has-text("product")',
    ]
    for sel in product_selectors:
        try:
            count = await page.locator(sel).count()
            if count > 0:
                first = page.locator(sel).first
                if await first.is_visible():
                    text = (await first.inner_text()).strip()[:60]
                    print(f"   ✅ {sel}: '{text}'")
        except:
            pass
    
    # Dump page data-testid elements
    print("\n📌 Step 7: All data-testid elements...")
    try:
        testids = await page.evaluate("""() => {
            const els = document.querySelectorAll('[data-testid]');
            return Array.from(els).map(el => ({
                tag: el.tagName,
                testid: el.getAttribute('data-testid'),
                text: el.innerText?.substring(0, 60),
                visible: el.offsetParent !== null
            })).filter(e => e.visible).slice(0, 40);
        }""")
        for t in testids:
            print(f"   {t['tag']}: testid='{t['testid']}' | text='{t.get('text', '').replace(chr(10), ' ')[:60]}'")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Also look for collection-related elements
    print("\n📌 Step 8: Looking for Collection elements...")
    coll_selectors = [
        '*:has-text("Collection")',
        '*:has-text("collection")',
        'button:has-text("Create collection")',
        'button:has-text("New collection")',
    ]
    for sel in coll_selectors:
        try:
            items = await page.locator(sel).all()
            for item in items[:3]:
                visible = await item.is_visible()
                if visible:
                    tag = await item.evaluate("el => el.tagName")
                    text = (await item.inner_text()).strip().replace('\n', ' ')[:80]
                    if tag in ("BUTTON", "A"):
                        print(f"   ✅ {sel}: [{tag}] '{text}'")
        except:
            pass
    
    print("\n✅ Done! Keeping browser open 25s...")
    await page.wait_for_timeout(25000)
    
    await context.close()
    await pw.stop()
    print("🛑 Closed.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

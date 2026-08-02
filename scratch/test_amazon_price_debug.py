import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.abspath("."))

from browser.browser_manager import BrowserManager

async def test_extract_price(manager, url):
    page = await manager.new_page()
    print(f"\n--- Testing URL: {url} ---")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)
        
        # Check Robot check
        title_text = await page.title()
        print("Page Title:", title_text)
        
        title_loc = page.locator("#productTitle").first
        if await title_loc.count() > 0:
            title = await title_loc.inner_text()
            print("Product Title:", title.strip()[:60])
        else:
            print("Product Title #productTitle: Not found")
            
        # Debug Price Selectors:
        selectors = [
            ("#corePriceDisplay_desktop_feature_div span.a-price.aok-align-center span.a-offscreen", "corePriceDisplay aok-align-center"),
            ("#corePriceDisplay_desktop_feature_div .priceToPay span.a-offscreen", "corePriceDisplay priceToPay"),
            ("#corePrice_feature_div .priceToPay span.a-offscreen", "corePrice priceToPay"),
            ("span.apexPriceToPay span.a-offscreen", "apexPriceToPay"),
            ("#apex_desktop .priceToPay span.a-offscreen", "apex_desktop priceToPay"),
            ("#priceblock_ourprice", "priceblock_ourprice"),
            ("#priceblock_dealprice", "priceblock_dealprice"),
            ("span.a-price:not(.a-text-price) span.a-offscreen", "span.a-price:not(.a-text-price)"),
            ("span.a-price span.a-offscreen", "span.a-price span.a-offscreen (Current selector)")
        ]
        
        for sel, name in selectors:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                txt_inner = await loc.inner_text()
                txt_content = await loc.get_attribute("textContent")
                print(f"  [{name}]: inner='{txt_inner}', content='{txt_content}'")
            else:
                print(f"  [{name}]: NOT FOUND")
                
        # Whole + fraction
        w_loc = page.locator(".priceToPay span.a-price-whole, #corePriceDisplay_desktop_feature_div span.a-price-whole, span.a-price:not(.a-text-price) span.a-price-whole").first
        if await w_loc.count() > 0:
            w_val = await w_loc.inner_text()
            f_loc = page.locator(".priceToPay span.a-price-fraction, #corePriceDisplay_desktop_feature_div span.a-price-fraction, span.a-price:not(.a-text-price) span.a-price-fraction").first
            f_val = await f_loc.inner_text() if await f_loc.count() > 0 else "00"
            print(f"  [Whole+Fraction]: ${w_val.strip()}{f_val.strip()}")
            
    except Exception as e:
        print("Error:", e)
    finally:
        await page.close()

urls = [
    "https://www.amazon.com/dp/B00V4L77R2", # Biodance Collagen Mask
    "https://www.amazon.com/dp/B09V7S1V85", # Beauty of Joseon Sunscreen
    "https://www.amazon.com/dp/B0C39M53CD", # e.l.f. Glow Reviver Lip Oil
]

async def main():
    manager = BrowserManager()
    await manager.initialize()
    try:
        for u in urls:
            await test_extract_price(manager, u)
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())

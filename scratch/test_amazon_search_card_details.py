import sys
sys.path.insert(0, ".")
import asyncio
import re
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    keywords = ["Biodance Bio Collagen Real Deep Mask", "Beauty of Joseon Sunscreen", "elf glow reviver lip oil", "Medicube Zero Pore Pad"]
    
    for kw in keywords:
        print(f"\n==========================================")
        print(f" Searching Amazon for: '{kw}'")
        print(f"==========================================")
        search_url = f"https://www.amazon.com/s?k={kw.replace(' ', '+')}&i=beauty"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)
        
        cards = page.locator('div[data-component-type="s-search-result"]')
        count = await cards.count()
        print(f"Found {count} cards on Amazon search page.")
        
        for i in range(min(count, 5)):
            card = cards.nth(i)
            
            # Title
            title_loc = card.locator('h2 a span, a h2 span, h2 span').first
            title = await title_loc.inner_text() if await title_loc.count() > 0 else "N/A"
            
            # Link
            link_loc = card.locator('a[href*="/dp/"]').first
            href = await link_loc.get_attribute("href") if await link_loc.count() > 0 else "N/A"
            
            # Image
            img_loc = card.locator('img.s-image').first
            img_url = await img_loc.get_attribute("src") if await img_loc.count() > 0 else "N/A"
            
            # Price
            price_loc = card.locator('span.a-price span.a-offscreen, span.a-price-whole').first
            price = "N/A"
            if await price_loc.count() > 0:
                p_text = await price_loc.get_attribute("textContent") or await price_loc.inner_text() or ""
                m = re.search(r'\$\s*(\d+(?:\.\d{2})?)', p_text)
                if m:
                    price = f"${m.group(1)}"
                else:
                    w_loc = card.locator('span.a-price-whole').first
                    f_loc = card.locator('span.a-price-fraction').first
                    if await w_loc.count() > 0:
                        w = re.sub(r'\D', '', await w_loc.inner_text() or "")
                        f = re.sub(r'\D', '', await f_loc.inner_text() or "00") if await f_loc.count() > 0 else "00"
                        if w:
                            price = f"${w}.{f[:2]}"
            
            # Rating & Reviews
            rat_loc = card.locator('i[class*="a-icon-star"], span[aria-label*="out of 5 stars"]').first
            rating = await rat_loc.get_attribute("aria-label") if await rat_loc.count() > 0 else "N/A"
            
            rev_loc = card.locator('span[aria-label*="ratings"], span.s-underline-text').first
            reviews = await rev_loc.inner_text() if await rev_loc.count() > 0 else "N/A"
            
            print(f"\nCandidate #{i+1}:")
            print(f"  Title   : {title[:50]}")
            print(f"  Price   : {price}")
            print(f"  Rating  : {rating}")
            print(f"  Reviews : {reviews}")
            print(f"  Image   : {img_url[:60]}")
            print(f"  Link    : {href[:60]}")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())

import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager
from browser.pinterest_client import PinterestClient

async def test():
    driver = BrowserManager()
    await driver.initialize()
    
    client = PinterestClient(driver)
    
    import os
    img_path = os.path.abspath("images/c390924f.jpg")
    title = "Korean Glass Skin Hydrating Serum | Sephora & Amazon Beauty Finds 2026"
    desc = "Achieve an effortless glowing skin look with this viral K-beauty serum on Amazon. Deeply hydrating, lightweight, and perfect for your daily clean girl skincare routine. Click to shop live price & read 15,000+ verified customer reviews on Amazon! 💾 Save this pin!"
    board = "K-Beauty Serums That Actually Work"
    link = "https://www.amazon.com/dp/B09JYS63DB?tag=savvyshop0965-20"
    alt = "A high-quality product shot of Beauty of Joseon Serum on a clean marble tray."
    
    print("\nExecuting Pinterest Pin Creation Test...")
    res = await client.create_pin(img_path, title, desc, board, link, alt)
    print(f"\nResult: {res}")
    
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())

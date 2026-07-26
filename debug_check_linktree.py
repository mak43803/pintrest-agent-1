import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    
    try:
        page = manager.context.pages[0]
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        
        print("Waiting for skeleton loaders to finish...")
        try:
            # Wait for something that indicates the shop loaded
            await page.wait_for_selector('text="Affiliate Products"', timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception:
            pass
            
        print("Extracting page text...")
        texts = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('h2, h3, div')).map(el => el.innerText).filter(t => t && t.includes('Gamer'));
        }''')
        print(f"Texts containing 'Gamer': {list(set(texts))}")
        
        # Take full page screenshot to see what's going on
        artifact_path = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_current_state.png"
        await page.screenshot(path=artifact_path, full_page=True)
        print(f"Screenshot taken: {artifact_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

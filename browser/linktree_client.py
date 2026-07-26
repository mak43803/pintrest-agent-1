"""
Linktree Client — High-level Linktree actions using Playwright.
===================================================================

Provides specific, high-level methods to interact with Linktree.
Encapsulates login via Google accounts and link adding automation.
"""

from __future__ import annotations

import logging
import os
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from browser.browser_manager import BrowserManager
from utils.exceptions import BrowserNavigationError, ElementNotFoundError

logger = logging.getLogger("pinterest_agent.browser.linktree")


class LinktreeClient:
    """
    High-level automation client for Linktree to add affiliate links.
    """

    BASE_URL = "https://linktr.ee"

    def __init__(self, manager: BrowserManager) -> None:
        self._manager = manager
        self._page: Page | None = None
        logger.info("LinktreeClient initialized.")

    async def _get_page(self) -> Page:
        """Return the active page, creating one if necessary."""
        if not self._page or self._page.is_closed():
            self._page = await self._manager.new_page()
        return self._page

    async def _dismiss_overlays_and_drawers(self, page: Page) -> None:
        """Dismiss any open left profile menu, drawers, or floating dialogs on Linktree."""
        try:
            # Send Escape to close active menus/dropdowns
            for _ in range(3):
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)

            # Check if left profile menu drawer is open (contains 'Create new Linktree' text)
            drawer_loc = page.locator('*:has-text("Create new Linktree"), *:has-text("Share feedback")')
            drawer_attempts = 0
            while await drawer_loc.count() > 0 and drawer_attempts < 6:
                drawer_attempts += 1
                logger.info(f"Left profile drawer is open (attempt {drawer_attempts}). Toggling profile header button (80, 118) to close...")
                await page.mouse.click(80, 118)
                await page.wait_for_timeout(500)
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(800)
                drawer_loc = page.locator('*:has-text("Create new Linktree"), *:has-text("Share feedback")')

            # Dismiss close buttons for tips/announcements
            for close_selector in [
                '[aria-label="Close"]',
                '[aria-label="Close dialog"]',
                'button:has-text("Close")',
                'button.close-button',
                '[data-testid="tips-dialog-done"]'
            ]:
                close_btns = await page.locator(close_selector).all()
                for btn in close_btns:
                    if await btn.is_visible():
                        logger.info(f"Clicking visible close button: {close_selector}")
                        await btn.click(force=True)
                        await page.wait_for_timeout(1000)
        except Exception as e:
            logger.debug(f"Error during dismiss overlays: {e}")

    async def is_logged_in(self) -> bool:
        """
        Check if currently authenticated in Linktree.
        Navigates to the admin panel and checks for dashboard visibility.
        """
        page = await self._get_page()
        try:
            logger.info("Checking Linktree login status...")
            # Check current URL first before navigating if already on admin
            current_url = page.url.lower()
            if "admin" in current_url and "login" not in current_url:
                add_btn_count = await page.locator('button:has-text("Add"), button:has-text("Edit"), [data-testid="admin-navigation-add-link"]').count()
                if add_btn_count > 0:
                    logger.info("Already on Linktree admin page and authenticated.")
                    return True

            await page.goto(f"{self.BASE_URL}/admin", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # If redirected to universal-login or login page, we are not logged in
            current_url = page.url.lower()
            if "login" in current_url or "universal-login" in current_url:
                logger.info("Not logged in to Linktree (redirected to login).")
                return False
                
            # If the current URL contains admin, we are authenticated (since Linktree redirects unauthenticated users)
            if "admin" in current_url:
                logger.info("Successfully authenticated to Linktree (URL contains 'admin').")
                return True
                
            # Look for Add link button or dashboard indicators
            add_btn_count = await page.locator('button:has-text("Add link"), button:has-text("Add"), [data-testid="admin-navigation-add-link"]').count()
            if add_btn_count > 0:
                logger.info("Successfully authenticated to Linktree (Found Add button).")
                return True
                
            logger.info("Dashboard elements not detected. Assuming not logged in.")
            return False
        except Exception as e:
            logger.debug(f"Error checking Linktree login: {e}")
            return False

    async def login(self) -> bool:
        """
        Perform login via Continue with Google.
        """
        page = await self._get_page()
        try:
            logger.info("Navigating to Linktree login page...")
            # Navigate to login page if not already there
            if "login" not in page.url.lower():
                try:
                    await page.goto(f"{self.BASE_URL}/login", wait_until="commit", timeout=60000)
                except Exception as e:
                    logger.warning(f"Navigating to login page warning: {e}")
                
            # Check if we were already logged in and got auto-redirected to the admin page
            current_url = page.url.lower()
            if "admin" in current_url and "login" not in current_url:
                logger.info("Redirected to Linktree admin page automatically. Already logged in!")
                return True
                
            logger.info("Waiting for Google login button to render...")
            
            # Formulate selectors that are commonly used for Google login
            google_selectors = [
                'button:has-text("Continue with Google")',
                'descope-button:has-text("Continue with Google")',
                ':text("Continue with Google")',
                'button[id*="google" i]',
                'descope-button#google-login',
                'button[data-testid="google-login-button"]',
                '[id*="google" i]'
            ]
            
            # Wait for any of the selectors to become visible (with up to 15s timeout)
            google_btn = None
            for selector in google_selectors:
                try:
                    loc = page.locator(selector).first
                    await loc.wait_for(state="attached", timeout=3000)
                    if await loc.count() > 0:
                        google_btn = loc
                        break
                except Exception:
                    continue
                    
            if not google_btn:
                # One last try with a broad selector and wait
                try:
                    await page.wait_for_selector('button:has-text("Continue with Google"), :text("Continue with Google"), [id*="google" i]', timeout=10000)
                    google_btn = page.locator('button:has-text("Continue with Google"), :text("Continue with Google"), [id*="google" i]').first
                except Exception as wait_exc:
                    logger.error(f"Timeout waiting for Google login button elements: {wait_exc}")
                    
            if not google_btn:
                logger.error("Could not find 'Continue with Google' button on Linktree login page.")
                return False

            logger.info("Clicking 'Continue with Google' button...")
            await google_btn.click(force=True)
            await page.wait_for_timeout(5000)

            # Check across all pages/popups for accounts.google.com
            target_page = page
            for p in page.context.pages:
                if "accounts.google.com" in p.url.lower():
                    target_page = p
                    break

            if "accounts.google.com" in target_page.url.lower():
                logger.info("On Google accounts page. Checking for account selectors...")
                # If there is a list of accounts, click the first one or the one matching "thehadit"
                for acc_selector in [
                    '[data-email*="thehadit" i]',
                    '[data-authuser="0"]',
                    'div[role="link"] div:has-text("thehadit")',
                    'div[role="link"]',
                    'li:has-text("thehadit")',
                    '[data-email]'
                ]:
                    acc_loc = target_page.locator(acc_selector).first
                    if await acc_loc.count() > 0:
                        logger.info(f"Clicking Google account: {acc_selector}")
                        await acc_loc.click(force=True)
                        await page.wait_for_timeout(5000)
                        break

            # Wait for admin redirect after Google authentication (allowing up to 60 seconds for Linktree's 'Just a minute' screen to settle)
            logger.info("Waiting for redirection to Linktree admin (allowing up to 60 seconds)...")
            for _ in range(60):
                current_url = page.url.lower()
                if "admin" in current_url and "login" not in current_url and "universal-login" not in current_url:
                    logger.info("Login successful! Navigated to Linktree admin.")
                    await page.wait_for_timeout(3000)
                    return True
                
                # Check if dashboard elements appeared even if URL hasn't updated yet
                try:
                    if await page.locator('button:has-text("Add"), button:has-text("Edit"), [data-testid="admin-navigation-add-link"]').count() > 0:
                        logger.info("Dashboard elements visible! Login successful.")
                        await page.wait_for_timeout(3000)
                        return True
                except Exception:
                    pass

                await page.wait_for_timeout(1000)

            # Re-check URL after loop
            current_url = page.url.lower()
            if "admin" in current_url and "login" not in current_url and "universal-login" not in current_url:
                logger.info("Login successful post-wait!")
                return True

            logger.error("Failed to redirect to admin page after login (timed out waiting for Linktree redirect).")
            return False

        except Exception as e:
            logger.error(f"Failed to log in to Linktree: {e}")
            return False

    async def add_link(self, title: str, url: str, category: str = "") -> bool:
        """
        Add a product link to the Linktree Shop page under a collection.
        """
        return await self.add_link_to_collection(title, url, category)

    async def add_link_to_collection(self, title: str, url: str, collection_name: str) -> bool:
        """
        Add the product affiliate link to Linktree Shop under a specific collection.
        If the collection doesn't exist, it creates it.
        """
        import time
        page = await self._get_page()
        try:
            logger.info(f"Adding product to Linktree Shop  │  title='{title}'  url='{url}'  collection='{collection_name}'")
            
            # Helper to navigate cleanly to Shop tab without triggering full reloads that drop session
            async def navigate_to_shop_tab():
                current_url = page.url.lower()
                if "login" in current_url or "universal-login" in current_url:
                    logger.warning("Redirected to login page. Performing Linktree login...")
                    logged_in = await self.login()
                    if not logged_in:
                        raise Exception("Failed to log in to Linktree via Google.")
                    await page.wait_for_timeout(3000)

                current_url = page.url.lower()
                # If authenticated on admin, attempt clicking the 'Shop' tab link in navbar (SPA navigation)
                if "admin" in current_url and "login" not in current_url:
                    shop_nav_selectors = [
                        'a[href*="/admin/shop"]',
                        'a:has-text("Shop")',
                        'button:has-text("Shop")',
                        'nav a:has-text("Shop")',
                        '[data-testid*="shop" i]'
                    ]
                    for nav_sel in shop_nav_selectors:
                        try:
                            shop_link = page.locator(nav_sel).filter(visible=True).first
                            if await shop_link.count() > 0:
                                logger.info(f"Clicking Shop navigation link: {nav_sel}")
                                await shop_link.click(force=True)
                                await page.wait_for_timeout(5000)
                                break
                        except Exception:
                            continue

                # If direct tab click was skipped or failed to change URL to admin/shop, try goto
                if "admin/shop" not in page.url.lower():
                    logger.info("Navigating to Linktree Shop Admin page URL...")
                    await page.goto(f"{self.BASE_URL}/admin/shop", wait_until="domcontentloaded", timeout=120000)
                    await page.wait_for_timeout(5000)

                # Re-check URL after navigation
                current_url = page.url.lower()
                if "login" in current_url or "universal-login" in current_url:
                    logger.warning("Redirected to login page post-navigation. Re-attempting login...")
                    logged_in = await self.login()
                    if not logged_in:
                        raise Exception("Failed to log in to Linktree via Google.")
                    await page.wait_for_timeout(3000)
                    for nav_sel in ['a[href*="/admin/shop"]', 'a:has-text("Shop")', 'button:has-text("Shop")']:
                        try:
                            shop_link = page.locator(nav_sel).filter(visible=True).first
                            if await shop_link.count() > 0:
                                await shop_link.click(force=True)
                                await page.wait_for_timeout(5000)
                                break
                        except Exception:
                            pass

            await navigate_to_shop_tab()

            # Dismiss any open overlays/drawers cleanly without clicking left profile button
            logger.info("Dismissing open drawers/overlays to unfreeze Shop dashboard render...")
            await self._dismiss_overlays_and_drawers(page)

            # Wait up to 3 minutes (180s) for Linktree Shop React rendering and GraphQL data hydration to complete
            logger.info("Waiting for Linktree Shop page React rendering and data loading to complete (up to 3 minutes)...")
            for attempt in range(120):  # 120 x 1.5s = 180 seconds (3 minutes)
                await page.wait_for_timeout(1500)
                current_url = page.url.lower()
                if "login" in current_url or "universal-login" in current_url:
                    logger.warning("Session lost during shop wait. Re-authenticating...")
                    await navigate_to_shop_tab()
                    break
                try:
                    # Check if the giant purple + Add button OR real collection cards have rendered on canvas (x > 230, y > 150)
                    loaded = await page.evaluate("""() => {
                        const btns = Array.from(document.querySelectorAll('button, [role="button"], a, div')).filter(el => {
                            const r = el.getBoundingClientRect();
                            const t = (el.innerText || el.textContent || '').trim().toLowerCase();
                            return r.x > 230 && r.y > 150 && r.width > 200 && (t === '+ add' || t === 'add' || t.includes('+ add'));
                        });
                        const mainTxt = (document.querySelector('main') || document.body).innerText || '';
                        const hasCards = mainTxt.includes('CTR') || mainTxt.includes('0 Clicks') || mainTxt.includes('1 Product');
                        return btns.length > 0 || hasCards;
                    }""")
                    if loaded:
                        logger.info(f"Linktree Shop page loaded successfully after {(attempt + 1) * 1.5:.1f} seconds!")
                        break
                    if (attempt + 1) % 10 == 0:
                        logger.info(f"Still waiting for Shop page to render ({int((attempt + 1) * 1.5)}s elapsed)...")
                except Exception as e:
                    logger.debug(f"Shop load check error: {e}")


            # Slowly scroll down to load any lazy-loaded collections on page
            try:
                logger.info("Scrolling all the way down to load all existing collections...")
                for _ in range(15):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(1500)
                # Scroll back to top
                await page.mouse.wheel(0, -30000)
                await page.wait_for_timeout(4000)
            except Exception as scroll_err:
                logger.debug(f"Scroll initialization skipped or failed: {scroll_err}")
                
            # Organize into specific collection
            if collection_name:
                import re
                collection_name_clean = re.sub(r'\s+\d+$', '', collection_name.strip())
                logger.info(f"Targeting Linktree collection: '{collection_name_clean}' (original: '{collection_name}')")
                
                # Helper function to find fuzzy card match
                async def find_fuzzy_collection_card(target_name: str):
                    target_words = [w.lower() for w in re.findall(r'[a-zA-Z0-9]+', target_name) if w]
                    if not target_words:
                        return None
                    
                    logger.info(f"Searching for card containing words: {target_words}")
                    
                    try:
                        js_code = """(target_name) => {
                            document.querySelectorAll('[data-bot-target]').forEach(el => el.removeAttribute('data-bot-target'));
                            
                            const rootEl = document.querySelector('main, [role="main"]') || document.body;
                            const targetLower = target_name.toLowerCase().trim();
                            const words = targetLower.split(/\\s+/).filter(w => w.length > 0);
                            
                            // Find all text elements containing all target words
                            const candidates = Array.from(rootEl.querySelectorAll('h1, h2, h3, h4, h5, p, span, div, button')).filter(e => {
                                if (!e.innerText) return false;
                                const txt = e.innerText.toLowerCase();
                                const allWordsPresent = words.every(w => txt.includes(w));
                                return allWordsPresent && txt.length < 150;
                            });

                            if (candidates.length === 0) return false;

                            // Pick the most specific element (smallest innerText length)
                            candidates.sort((a, b) => a.innerText.length - b.innerText.length);
                            candidates[0].setAttribute('data-bot-target', 'true');
                            return true;
                        }"""
                        
                        found = await page.evaluate(js_code, target_name)
                        if found:
                            card_locator = page.locator('[data-bot-target="true"]').first
                            logger.info(f"Match Found via JS for '{target_name}' card.")
                            return card_locator
                    except Exception as e:
                        logger.warning(f"JS Card lookup strategy failed: {e}")
                        
                    return None

                # Final URL check before searching for collection
                if "login" in page.url.lower() or "universal-login" in page.url.lower():
                    logger.warning("Detected login page before collection lookup! Triggering re-login...")
                    await navigate_to_shop_tab()

                # Search first for exact collection name, then for cleaned collection name
                card = await find_fuzzy_collection_card(collection_name)
                if not card:
                    card = await find_fuzzy_collection_card(collection_name_clean)

                coll_exists = False
                if card:
                    try:
                        await card.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1500)
                        coll_exists = True
                        logger.info(f"Existing collection card for '{collection_name}' found.")
                    except Exception as scroll_err:
                        logger.debug(f"Scroll check error: {scroll_err}")
                
                if not coll_exists:
                    logger.info(f"Collection '{collection_name_clean}' not found on dashboard.")
                    logger.info("Scrolling back to top of all containers to bring '+ Add' button into viewport...")
                    await page.evaluate("""() => {
                        window.scrollTo(0, 0);
                        document.documentElement.scrollTop = 0;
                        document.body.scrollTop = 0;
                        const scrollableDivs = Array.from(document.querySelectorAll('div, main, section')).filter(el => el.scrollHeight > el.clientHeight);
                        for (const d of scrollableDivs) {
                            d.scrollTop = 0;
                        }
                    }""")
                    await page.wait_for_timeout(3000)

                    # Dismiss any accidental dialogs (Share your Linktree, etc.) before looking for + Add button
                    for close_sel in ['[aria-label="Close"]', 'button[aria-label="Close"]', 'button:has-text("Close")', 'button:has-text("Got it")', 'button:has-text("Done")']:
                        try:
                            close_btns = page.locator(close_sel).filter(visible=True)
                            if await close_btns.count() > 0:
                                logger.info(f"Closing accidental dialog via: {close_sel}")
                                await close_btns.first.click(force=True)
                                await page.wait_for_timeout(1000)
                                break
                        except Exception:
                            pass

                    coll_btn = None
                    for add_attempt in range(5):
                        # Check if "Add to your Shop" modal is already open
                        dialog_open = await page.locator('[role="dialog"]:visible, *:has-text("Add to your Shop")').filter(visible=True).count() > 0
                        if not dialog_open:
                            logger.info("Searching for main canvas purple '+ Add' button via JS...")
                            found_btn_info = await page.evaluate("""() => {
                                // Scan ALL elements for the one with '+ add' or 'add' text in main canvas (x > 200, y > 50)
                                const allEls = Array.from(document.querySelectorAll('button, [role="button"], a, div'));
                                let candidates = [];
                                for (const el of allEls) {
                                    const r = el.getBoundingClientRect();
                                    if (r.width < 80 || r.height < 15) continue;
                                    const t = (el.innerText || el.textContent || '').trim().toLowerCase();
                                    // Canvas area: x > 200, y > 50 (main canvas area)
                                    if (r.x > 200 && r.y > 50 && (t === '+ add' || t === 'add' || t.includes('+ add'))) {
                                        candidates.push({
                                            x: r.x, y: r.y, w: r.width, h: r.height,
                                            txt: (el.innerText || el.textContent || '').trim().substring(0, 50),
                                            tag: el.tagName,
                                            cls: el.className.toString().substring(0, 50)
                                        });
                                    }
                                }
                                // Sort by width descending (widest candidate = large purple Add pill bar)
                                candidates.sort((a, b) => b.w - a.w);
                                return candidates;
                            }""")
                            logger.info(f"Canvas add candidates (attempt {add_attempt+1}): {found_btn_info}")

                            if found_btn_info:
                                best = found_btn_info[0]
                                logger.info(f"Clicking best canvas add candidate: {best}")
                                cx = best['x'] + best['w'] / 2
                                cy = best['y'] + best['h'] / 2
                                await page.mouse.click(cx, cy)
                                logger.info(f"Clicked at coordinates ({cx:.0f}, {cy:.0f})")
                            else:
                                # Fallback locator try via Playwright
                                try:
                                    add_btn_pw = page.locator('button:has-text("+ Add"), button:has-text("Add")').filter(visible=True)
                                    cnt = await add_btn_pw.count()
                                    for i in range(cnt):
                                        c = add_btn_pw.nth(i)
                                        bb = await c.bounding_box()
                                        if bb and bb['x'] > 200 and bb['y'] > 50:
                                            logger.info(f"Found + Add button via Playwright locator at bbox={bb}. Clicking...")
                                            await c.click(force=True)
                                            break
                                except Exception as pw_err:
                                    logger.warning(f"Playwright locator fallback error: {pw_err}")

                            await page.wait_for_timeout(4000)
                        # Check for 'Collection' menu option in opened Add menu ("Add to your Shop" modal)
                        logger.info("Selecting 'Collection' option from Add menu...")
                        try:
                            # Try native text lookup for Option 1 card
                            card_opt = page.get_by_text("Organize Linked products").first
                            if await card_opt.is_visible():
                                coll_btn = card_opt
                                logger.info("Found Collection option card via page.get_by_text('Organize Linked products').")
                                break
                        except Exception:
                            pass

                        if not coll_btn:
                            locs = page.locator('*:has-text("Organize Linked products")').filter(visible=True)
                            count = await locs.count()
                            best_cand = None
                            best_len = 999999
                            for i in range(count):
                                cand = locs.nth(i)
                                txt = (await cand.inner_text()).strip()
                                if "organize linked products" in txt.lower() and len(txt) < best_len:
                                    best_len = len(txt)
                                    best_cand = cand

                            if best_cand:
                                coll_btn = best_cand
                                logger.info(f"Found exact Collection option card (inner text length: {best_len}).")
                                break

                    if not coll_btn:
                        logger.info("Fallback lookup for 'Collection' text...")
                        for sel in [
                            'button:has-text("Collection")',
                            'div[role="button"]:has-text("Collection")',
                            'p:has-text("Collection")',
                            'span:has-text("Collection")'
                        ]:
                            loc = page.locator(sel).filter(visible=True).first
                            if await loc.count() > 0:
                                coll_btn = loc
                                break

                    if not coll_btn:
                        raise Exception("Could not locate 'Collection' option button in the Add menu!")

                    await coll_btn.wait_for(state="visible", timeout=10000)
                    await coll_btn.click(force=True)
                    await page.wait_for_timeout(8000)
                else:
                    # Linktree UI update: Click the collection card itself to open it
                    logger.info(f"Clicking the collection card '{collection_name_clean}' to open it...")
                    await card.click(force=True)
                    await page.wait_for_timeout(8000)
                    
                    # Inside the opened collection modal, click the '+ Add' button
                    logger.info("Locating the '+ Add' button inside the collection modal...")
                    modal_add_btn = None
                    for selector in [
                        'dialog:visible button:has-text("+ Add")',
                        'dialog:visible button:has-text("Add products")',
                        'dialog:visible button:has-text("Add")',
                        'button:has-text("+ Add")',
                        'button:has-text("Add")'
                    ]:
                        loc = page.locator(selector).filter(visible=True).first
                        if await loc.count() > 0:
                            modal_add_btn = loc
                            break
                    
                    if modal_add_btn:
                        await modal_add_btn.click(force=True)
                        await page.wait_for_timeout(8000)
                    else:
                        raise Exception("Could not find '+ Add' button inside the opened collection modal!")

                title_already_filled = False
                if not coll_exists:
                    # Check for Linktree's 'Title First' UI variant (asks for title + Continue button before products)
                    await page.wait_for_timeout(4000)
                    try:
                        continue_btn = page.locator('dialog:visible button:has-text("Continue")').filter(visible=True).first
                        if await continue_btn.count() > 0:
                            logger.info("Detected 'Title First' UI variant! Filling collection title first...")
                            title_first_input = page.locator('dialog:visible input[type="text"]').filter(visible=True).first
                            if await title_first_input.count() > 0:
                                await title_first_input.fill(collection_name_clean)
                                await page.wait_for_timeout(2000)
                                await continue_btn.click(force=True)
                                await page.wait_for_timeout(8000)
                                title_already_filled = True
                    except Exception as e:
                        logger.debug(f"Title First check skipped: {e}")

                # COMMON STEP FOR BOTH (NEW UI FLOW):
                # Now we should be on the "Search products or paste a link" screen
                logger.info("Pasting product affiliate link in URL search input...")
                
                # First wait for the dialog/modal to fully render
                await page.wait_for_timeout(5000)
                
                # Use get_by_placeholder to find the visible search input safely
                search_input = None
                for _ in range(45):
                    loc = page.locator('input[placeholder*="Search products"], input[placeholder*="Paste URL"], input[type="url"]').filter(visible=True).first
                    if await loc.count() > 0:
                        search_input = loc
                        break
                    await page.wait_for_timeout(2000)
                
                if not search_input:
                    raise Exception("Timeout waiting for Search Input to become visible.")
                
                await search_input.focus()
                await page.wait_for_timeout(2000)
                await search_input.press_sequentially(url, delay=50)
                await page.wait_for_timeout(8000)
                
                logger.info("Locating product search result card container...")
                target = None
                
                # 1. Search via JS evaluator for product result container/row inside modal below search input
                for _ in range(15):  # Wait up to 30 seconds for product card to render
                    try:
                        js_target_handle = await page.evaluate_handle("""() => {
                            const modals = Array.from(document.querySelectorAll('[role="dialog"], dialog')).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
                            const modal = modals.length > 0 ? modals[modals.length - 1] : document;
                            const input = modal.querySelector('input');
                            const inputBottom = input ? input.getBoundingClientRect().bottom : 100;
                            
                            const elements = Array.from(modal.querySelectorAll('div, button, li, a, [role="button"]'));
                            
                            // Strategy A: Find row/container with product text / Amazon / price below search input
                            for (const el of elements) {
                                const r = el.getBoundingClientRect();
                                if (r.width >= 150 && r.height >= 40 && r.y >= inputBottom - 10 && r.y < window.innerHeight - 80) {
                                    const txt = (el.innerText || el.textContent || '').trim();
                                    if (txt.includes('Amazon') || txt.includes('$') || txt.length > 15) {
                                        return el;
                                    }
                                }
                            }
                            
                            // Strategy B: Any container div below input with product card dimensions
                            for (const el of elements) {
                                const r = el.getBoundingClientRect();
                                if (r.width >= 200 && r.height >= 40 && r.height <= 220 && r.y >= inputBottom + 5 && r.y < window.innerHeight - 80) {
                                    return el;
                                }
                            }
                            return null;
                        }""")
                        if js_target_handle and await js_target_handle.as_element():
                            target = js_target_handle.as_element()
                            break
                    except Exception as err:
                        logger.debug(f"JS product card locator error: {err}")
                    await page.wait_for_timeout(2000)

                # 2. Fallback Playwright locators for product card
                if not target:
                    for sel in [
                        'dialog:visible button:has-text("+")',
                        'dialog:visible button[aria-label*="Add" i]',
                        'dialog:visible button:has-text("Amazon")',
                        'button:has-text("+")',
                        'button:has-text("Amazon")'
                    ]:
                        loc = page.locator(sel).filter(visible=True).first
                        if await loc.count() > 0:
                            target = loc
                            break

                if target:
                    logger.info("Clicking product card container to select product...")
                    try:
                        box = await target.bounding_box()
                        if box:
                            cx = box["x"] + box["width"] / 2
                            cy = box["y"] + box["height"] / 2
                            logger.info(f"Clicking product card at coordinates ({cx:.0f}, {cy:.0f})...")
                            await page.mouse.click(cx, cy)
                            await page.wait_for_timeout(1000)
                    except Exception as m_err:
                        logger.debug(f"Mouse click error on product card: {m_err}")
                    try:
                        await target.click(force=True)
                    except Exception:
                        try:
                            await target.evaluate("(el) => el.click()")
                        except Exception:
                            pass
                    await page.wait_for_timeout(3000)
                else:
                    logger.warning("Product card container target not found directly, proceeding to check Continue button...")

                # STEP A: Click purple 'Continue' button on search sub-modal (as seen in video at 00:23)
                logger.info("Locating and clicking purple 'Continue' button on product selection sub-modal...")
                continue_btn = None
                for _ in range(10):  # Wait up to 20 seconds
                    for selector in [
                        'dialog:visible button:has-text("Continue")',
                        '[role="dialog"]:visible button:has-text("Continue")',
                        'button:has-text("Continue")'
                    ]:
                        locs = page.locator(selector).filter(visible=True)
                        count = await locs.count()
                        for i in range(count):
                            cand = locs.nth(i)
                            is_disabled = await cand.get_attribute("disabled")
                            aria_disabled = await cand.get_attribute("aria-disabled")
                            if is_disabled is None and aria_disabled != "true":
                                continue_btn = cand
                                break
                        if continue_btn:
                            break
                    if continue_btn:
                        break
                    await page.wait_for_timeout(2000)

                if continue_btn:
                    logger.info("Clicking purple 'Continue' button on sub-modal...")
                    try:
                        box = await continue_btn.bounding_box()
                        if box:
                            cx = box["x"] + box["width"] / 2
                            cy = box["y"] + box["height"] / 2
                            await page.mouse.click(cx, cy)
                            await page.wait_for_timeout(1000)
                    except Exception:
                        pass
                    try:
                        await continue_btn.click(force=True)
                    except Exception:
                        try:
                            await continue_btn.evaluate("(el) => el.click()")
                        except Exception:
                            pass
                    await page.wait_for_timeout(4000)
                    
                # STEP B: IF WE ARE CREATING A NEW COLLECTION, SET THE TITLE NOW!
                if not coll_exists and not title_already_filled:
                    logger.info(f"Filling 'Collection title' with '{collection_name_clean}'...")
                    title_input = None
                    for selector in [
                        'dialog:visible input[placeholder*="title" i]',
                        'dialog:visible input[placeholder*="collection" i]',
                        'dialog:visible input[name*="title" i]',
                        'dialog:visible input[value=""]',
                        'dialog:visible input[type="text"]',
                        'input[placeholder*="title" i]',
                        'input[placeholder*="collection" i]'
                    ]:
                        locs = page.locator(selector).filter(visible=True)
                        count = await locs.count()
                        for i in range(count):
                            cand = locs.nth(i)
                            if await cand.is_visible():
                                title_input = cand
                                break
                        if title_input:
                            break

                    if title_input:
                        await title_input.click()
                        await title_input.fill(collection_name_clean)
                        await page.wait_for_timeout(3000)
                        logger.info(f"Successfully set collection title to: '{collection_name_clean}'")
                
                # STEP C: Click final purple 'Save' button on parent collection modal (as seen in video at 00:29)
                logger.info("Locating and clicking final purple 'Save' button in parent collection modal...")
                save_btn = None
                
                # 1. Search via JS evaluator in the active modal container for exact 'Save' button
                try:
                    js_handle = await page.evaluate_handle("""() => {
                        const modals = Array.from(document.querySelectorAll('[role="dialog"], dialog, div[class*="modal"], div[class*="overlay"], div[class*="fixed"]')).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
                        const container = modals.length > 0 ? modals[modals.length - 1] : document;
                        const btns = Array.from(container.querySelectorAll('button, [role="button"], input[type="submit"], div[role="button"]')).filter(b => b.offsetWidth > 0 && b.offsetHeight > 0);
                        
                        // Priority 1: Exact text 'save'
                        for (const b of btns) {
                            const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                            if (txt === 'save') return b;
                        }
                        // Priority 2: Text contains 'save' or 'done'
                        for (const b of btns) {
                            const txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                            if (txt.includes('save') || txt === 'done' || txt.includes('save collection')) return b;
                        }
                        // Priority 3: Primary purple background button
                        for (const b of btns) {
                            const bg = window.getComputedStyle(b).backgroundColor || '';
                            if (bg.includes('129') || bg.includes('117') || bg.includes('128') || bg.includes('138') || b.type === 'submit') return b;
                        }
                        return null;
                    }""")
                    if js_handle and await js_handle.as_element():
                        save_btn = js_handle.as_element()
                except Exception as js_err:
                    logger.debug(f"JS Save button locator error: {js_err}")

                # 2. Fallback Playwright locators for Save button
                if not save_btn:
                    for _ in range(8):  # Wait up to 16 seconds
                        for selector in [
                            'dialog:visible button:has-text("Save")',
                            'button:has-text("Save")',
                            'dialog:visible button:has-text("Done")',
                            'button:has-text("Done")',
                            'dialog:visible button:has-text("Save collection")',
                            'button:has-text("Save collection")',
                            'dialog:visible button[type="submit"]'
                        ]:
                            locs = page.locator(selector).filter(visible=True)
                            count = await locs.count()
                            for i in range(count):
                                cand = locs.nth(i)
                                is_disabled = await cand.get_attribute("disabled")
                                aria_disabled = await cand.get_attribute("aria-disabled")
                                if is_disabled is None and aria_disabled != "true":
                                    save_btn = cand
                                    break
                            if save_btn:
                                break
                        if save_btn:
                            break
                        await page.wait_for_timeout(2000)

                if save_btn:
                    btn_txt = ""
                    try:
                        btn_txt = (await save_btn.inner_text()).strip()
                    except:
                        pass
                    logger.info(f"Clicking final purple '{btn_txt or 'Save'}' button...")
                    
                    # Real Hardware Mouse Click on Save button center
                    try:
                        box = await save_btn.bounding_box()
                        if box:
                            cx = box["x"] + box["width"] / 2
                            cy = box["y"] + box["height"] / 2
                            logger.info(f"Clicking purple Save button at coordinates ({cx:.0f}, {cy:.0f})...")
                            await page.mouse.click(cx, cy)
                            await page.wait_for_timeout(1000)
                    except Exception as mouse_err:
                        logger.debug(f"Hardware mouse click failed: {mouse_err}")
                    
                    # Secondary force click & JS click fallbacks
                    try:
                        await save_btn.click(force=True)
                    except Exception:
                        try:
                            await save_btn.evaluate("(el) => el.click()")
                        except Exception:
                            pass
                    await page.wait_for_timeout(5000)
                else:
                    logger.warning("Save button not found, checking if modal dialog closed automatically...")
                    # Check if modal dialog has already closed automatically upon adding product
                    dialog_count = await page.locator('[role="dialog"]:visible, dialog:visible').count()
                    if dialog_count == 0:
                        logger.info("Product modal closed automatically upon selection. Product added successfully!")
                    else:
                        # Try closing any remaining modal cleanly
                        logger.warning("Save/Done button not found, but modal dialog is still open. Attempting fallback close/click...")
                        try:
                            close_btn = page.locator('[role="dialog"]:visible button[aria-label*="Close"], dialog:visible button:has-text("Done")').filter(visible=True).first
                            if await close_btn.count() > 0:
                                await close_btn.click(force=True)
                                await page.wait_for_timeout(3000)
                        except Exception:
                            pass
                
            logger.info("Waiting 25 seconds for product to save to Linktree...")
            await page.wait_for_timeout(25000)
            
            # Save screenshot for confirmation
            try:
                screenshot_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\linktree_after_add.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"Linktree post-addition screenshot saved to: {screenshot_path}")
            except Exception as ss_exc:
                logger.warning(f"Failed to capture post-addition screenshot: {ss_exc}")
                
            logger.info("Product added successfully to Linktree Shop!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add product to Linktree Shop: {e}")
            try:
                err_ss = f"logs/memory_error_{int(time.time())}.png"
                await page.screenshot(path=err_ss)
                logger.info(f"Linktree error screenshot saved to: {err_ss}")
            except:
                pass
            raise

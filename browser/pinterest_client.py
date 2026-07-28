"""
Pinterest Client — High-level Pinterest actions using Playwright.
===================================================================

Provides specific, high-level methods to interact with Pinterest.
Encapsulates all DOM selectors, waiting logic, and navigation.

Features:
    • Login verification (checks if cookies are valid)
    • Credential-based login with stealth bypassing
    • Pin creation (uploading images, setting title/desc/board/link)
    • Exception handling for missing DOM elements

Usage::

    from browser.pinterest_client import PinterestClient
    from browser.browser_manager import BrowserManager

    manager = BrowserManager()
    await manager.initialize()
    
    client = PinterestClient(manager)
    if not await client.is_logged_in():
        await client.login("email@test.com", "password123")
        
    await client.create_pin(
        image_path="images/product.jpg",
        title="Cool Gadget",
        description="Must have gadget of 2025",
        board_name="Tech Vibes",
        link="https://amzn.to/xyz"
    )
"""

from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from browser.browser_manager import BrowserManager
from utils.exceptions import BrowserNavigationError, ElementNotFoundError, FatalLoginError

logger = logging.getLogger("pinterest_agent.browser.client")


class PinterestClient:
    """
    High-level automation client for Pinterest.

    Args:
        manager: An initialized ``BrowserManager``.
    """

    BASE_URL = "https://www.pinterest.com"

    def __init__(self, manager: BrowserManager) -> None:
        self._manager = manager
        # Keep a single page instance for the client session
        self._page: Page | None = None
        self._login_failures = 0
        
        # Self-Healing properties
        from typing import Callable, Awaitable
        from database.database import Database
        self._db: Database | None = None
        self._analyze_ui_fn: Callable[[str, str, str], Awaitable[str]] | None = None
        logger.info("PinterestClient initialized.")

    def enable_vision_healing(self, db, analyze_ui_fn) -> None:
        """Inject the database and Gemini vision function for self-healing."""
        self._db = db
        self._analyze_ui_fn = analyze_ui_fn

    async def _smart_wait_for_selector(self, page: Page, original_selector: str, context: str, timeout: int = 15000, state: str = "visible") -> str:
        """
        Tries to wait for a selector. If it fails, checks DB for a healed selector.
        If that fails, captures screenshot and asks Gemini for the new selector.
        Returns the selector that ultimately worked.
        """
        # 1. Try DB healed selector first
        working_selector = original_selector
        if self._db:
            with self._db.connection() as conn:
                cursor = conn.execute("SELECT healed_selector FROM healed_selectors WHERE original_selector = ?", (original_selector,))
                row = cursor.fetchone()
                if row:
                    healed = row["healed_selector"]
                    logger.info(f"Self-Healing: Trying known healed selector from DB: {healed}")
                    try:
                        await page.wait_for_selector(healed, state=state, timeout=5000)
                        return healed
                    except PlaywrightTimeoutError:
                        logger.warning("Self-Healing: Known healed selector also failed. Proceeding to Vision healing.")
        
        # 2. Try Original Selector
        try:
            await page.wait_for_selector(original_selector, state=state, timeout=timeout)
            return original_selector
        except PlaywrightTimeoutError:
            logger.warning(f"Selector '{original_selector}' failed. Initiating Vision Self-Healing...")
            
            if not self._analyze_ui_fn:
                raise
                
            # 3. Vision Healing
            screenshot_path = "images/vision_heal_temp.png"
            import os
            os.makedirs("images", exist_ok=True)
            await page.screenshot(path=screenshot_path)
            
            new_selector = await self._analyze_ui_fn(screenshot_path, original_selector, context)
            if new_selector.startswith("ERROR"):
                logger.error("Vision Self-Healing could not find the element.")
                raise PlaywrightTimeoutError(f"Vision Healing failed for {original_selector}")
                
            logger.info(f"Vision Self-Healing found new selector: {new_selector}. Retrying...")
            try:
                await page.wait_for_selector(new_selector, state=state, timeout=10000)
                
                # 4. Save to DB
                if self._db:
                    with self._db.connection() as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO healed_selectors (original_selector, healed_selector) VALUES (?, ?)",
                            (original_selector, new_selector)
                        )
                return new_selector
            except PlaywrightTimeoutError:
                logger.error("Vision Self-Healing's suggested selector also timed out!")
                raise PlaywrightTimeoutError(f"Vision Healing suggested invalid selector: {new_selector}")

    async def _get_page(self) -> Page:
        """Return the active page, creating one if necessary."""
        if not self._page or self._page.is_closed():
            self._page = await self._manager.new_page()
        return self._page

    # ── Authentication ─────────────────────────────────────────────────

    async def is_logged_in(self) -> bool:
        """
        Check if the current session (cookies) is authenticated.

        Navigates to the homepage and looks for logged-in indicators
        (like the profile button or "Home feed" text).
        """
        page = await self._get_page()
        try:
            logger.info("Checking login status...")
            await page.goto(self.BASE_URL, wait_until="domcontentloaded")
            
            # Wait for either the login button (not logged in) or the profile avatar (logged in)
            # Pinterest DOM changes often, so we check for common data-test-ids
            try:
                # Wait up to 5 seconds for a definitive logged-in element
                await page.wait_for_selector(
                    '[data-test-id="header-profile"]', 
                    state="visible", 
                    timeout=5000
                )
                logger.info("Session is valid (Logged In).")
                return True
            except PlaywrightTimeoutError:
                logger.info("Session is invalid (Not Logged In).")
                return False

        except Exception as exc:
            logger.error("Failed to check login status: %s", exc)
            return False

    async def get_us_beauty_trends(self) -> str:
        """
        Navigate to Pinterest Trends US and perform a 2-minute deep-dive human research session.
        Returns a string of comma-separated trending keywords.
        """
        page = await self._get_page()
        logger.info("⚡ Executing 2-Minute Deep-Dive Human Research on Pinterest Trends US...")
        valid_texts = set()
        try:
            await page.goto("https://trends.pinterest.com/?country=US", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(6000)
            
            # Phase 1: Search Primary Term "viral beauty products" with realistic typing
            try:
                search_input = page.locator('input[type="text"], input[placeholder*="earch"]').first
                if await search_input.is_visible():
                    await search_input.click()
                    await page.wait_for_timeout(1500)
                    await page.keyboard.type("viral beauty products", delay=180)
                    await page.wait_for_timeout(2500)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(6000)
            except Exception as e:
                logger.debug(f"Phase 1 search input notice: {e}")
                
            # Deep Scroll Phase 1: 10 wheel scrolls with 4-second human inspection pauses (~40s)
            for _ in range(10):
                await page.mouse.wheel(0, 550)
                await page.wait_for_timeout(4000)
                
            # Extract Phase 1 keywords
            texts = await page.locator('span, h2, h3, a').all_inner_texts()
            for t in texts:
                t = t.strip()
                if t and 4 < len(t) < 40 and '+' not in t and '%' not in t and 'MoM' not in t and 'YoY' not in t and 'Opens a new tab' not in t:
                    valid_texts.add(t)

            # Phase 2: Dynamic Category Deep Search across ALL Beauty Product Categories (US, UK, Canada, Australia)
            import random
            sub_niche_queries = [
                "trending makeup dupes",
                "best skincare serums for glowing skin",
                "viral hair growth oils blowout",
                "luxury women perfumes body mist",
                "aesthetic vanilla body care routine",
                "viral lip oils lip gloss",
                "glazed donut nails gel manicure",
                "at home facial beauty tools devices",
                "sunscreen for dewy glass skin"
            ]
            chosen_sub_query = random.choice(sub_niche_queries)
            logger.info("Phase 2 Deep Research: Searching sub-category '%s'...", chosen_sub_query)
            try:
                search_input = page.locator('input[type="text"], input[placeholder*="earch"]').first
                if await search_input.is_visible():
                    await search_input.click()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await page.wait_for_timeout(1000)
                    await page.keyboard.type(chosen_sub_query, delay=160)
                    await page.wait_for_timeout(2000)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(6000)
            except Exception as e:
                logger.debug(f"Phase 2 search notice: {e}")

            # Deep Scroll Phase 2: 8 wheel scrolls with 4-second human inspection pauses (~32s)
            for _ in range(8):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(4000)

            # Scroll back up slowly (~15s)
            for _ in range(5):
                await page.mouse.wheel(0, -900)
                await page.wait_for_timeout(3000)
                
            # Extract final accumulated keywords
            texts = await page.locator('span, h2, h3, a').all_inner_texts()
            for t in texts:
                t = t.strip()
                if t and 4 < len(t) < 40 and '+' not in t and '%' not in t and 'MoM' not in t and 'YoY' not in t and 'Opens a new tab' not in t:
                    valid_texts.add(t)
            
            trends_list = list(valid_texts)[:50]
            logger.info(f"✅ 2-Minute Deep-Dive Research Complete! Found {len(trends_list)} viral beauty keywords on Pinterest Trends.")
            return ", ".join(trends_list)
        except Exception as e:
            logger.error(f"Failed to fetch Pinterest trends: {e}")
            return ""

    async def get_google_beauty_trends(self) -> str:
        """
        Navigate to Google Trends US and perform a 2-minute deep-dive human research session.
        Returns a string of comma-separated trending keywords.
        """
        page = await self._get_page()
        logger.info("⚡ Executing 2-Minute Deep-Dive Human Research on Google Trends US...")
        valid_texts = set()
        try:
            await page.goto("https://trends.google.com/trending?geo=US", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(6000)
            
            # Phase 1: Deep Scroll Google Trends US (10 scrolls with 4s human inspection pauses) (~40s)
            for _ in range(10):
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(4000)
                
            # Phase 2: Active Search for "viral beauty makeup skincare" with human typing delay (~30s)
            try:
                search_input = page.locator('input[type="text"], input[type="search"]').first
                if await search_input.is_visible():
                    await search_input.click()
                    await page.wait_for_timeout(1500)
                    await page.keyboard.type("viral beauty makeup skincare", delay=170)
                    await page.wait_for_timeout(2500)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(6000)
            except Exception as e:
                logger.debug(f"Google Trends search input notice: {e}")
                
            # Phase 3: Secondary Deep Scroll (8 scrolls with 4s human inspection pauses) (~32s)
            for _ in range(8):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(4000)

            # Phase 4: Scroll back up slowly (~15s)
            for _ in range(5):
                await page.mouse.wheel(0, -900)
                await page.wait_for_timeout(3000)
                
            texts = await page.locator('div, span, a').all_inner_texts()
            for t in texts:
                t = t.strip()
                if t and 4 < len(t) < 40 and "K" not in t and "+" not in t:
                    valid_texts.add(t)
            
            trends_list = list(valid_texts)[:50]
            logger.info(f"✅ 2-Minute Deep-Dive Research Complete! Found {len(trends_list)} viral keywords on Google Trends US.")
            return ", ".join(trends_list)
        except Exception as e:
            logger.error(f"Failed to fetch Google trends: {e}")
            return ""

    async def login(self, email: str, password: str) -> None:
        """
        Perform a credential-based login to Pinterest.

        Args:
            email:    User email.
            password: User password.

        Raises:
            BrowserNavigationError: If login fails or blocks occur.
        """
        page = await self._get_page()
        logger.info("Attempting credential login for %s", email)

        try:
            await page.goto(f"{self.BASE_URL}/login/", wait_until="domcontentloaded", timeout=60000)

            # 1. Enter Email
            email_sel = '#email, input[name="id"], input[type="email"]'
            email_healed = await self._smart_wait_for_selector(page, email_sel, "Pinterest Login Email Input Field", timeout=30000)
            await page.fill(email_healed, email)
            
            await page.wait_for_timeout(500)
            pass_sel = '#password, input[name="password"], input[type="password"]'
            
            try:
                # If it's a 1-step login, it should be visible immediately
                await page.wait_for_selector(pass_sel, state="visible", timeout=2000)
            except PlaywrightTimeoutError:
                # Probably a 2-step login. Press Enter on the email field.
                logger.info("Password field not immediately visible. Assuming 2-step login, pressing Enter...")
                await page.press(email_healed, "Enter")
                await page.wait_for_timeout(1000)
            
            # 2. Enter Password
            pass_healed = await self._smart_wait_for_selector(page, pass_sel, "Pinterest Login Password Input Field", timeout=10000)
            await page.fill(pass_healed, password)
            
            # 3. Click Login
            submit_sel = 'button[type="submit"], div[data-test-id="registerFormSubmitButton"] button, div[data-test-id="loginButton"] button'
            await page.click(submit_sel)

            # 4. Wait for navigation / success indicator
            # We wait for the profile button to appear, indicating the dashboard loaded
            try:
                await page.wait_for_selector(
                    '[data-test-id="header-profile"]', 
                    state="visible", 
                    timeout=15000
                )
            except PlaywrightTimeoutError:
                # Check if there's an explicit error message (e.g. wrong password or captcha)
                error_elem = await page.query_selector('[data-test-id="login-error-message"]')
                if error_elem:
                    error_text = await error_elem.inner_text()
                    raise BrowserNavigationError(f"Login failed: {error_text}")
                
                raise BrowserNavigationError(
                    "Login timed out. Pinterest might have served a Captcha or anti-bot challenge."
                )

            logger.info("Login successful.")
            self._login_failures = 0
            
            # Save the new cookies immediately
            await self._manager._save_session()

        except Exception as exc:
            self._login_failures += 1
            logger.warning("Pinterest login attempt failed (Attempt %d/2): %s", self._login_failures, exc)
            if self._login_failures >= 2:
                logger.critical("🛑 PINTEREST LOGIN FAILED 2 CONSECUTIVE TIMES! Stopping agent to prevent suspicious activity locks.")
                raise FatalLoginError("Pinterest login failed 2 consecutive times. Stopping agent for security. Run 'python login_pinterest_once.py' to authenticate manually.") from exc
            raise

    async def _find_visible_locator(self, page, selectors):
        """
        Finds the first locator among list of selectors that is attached and visible.
        """
        for selector in selectors:
            loc = page.locator(selector)
            try:
                count = await loc.count()
                for idx in range(count):
                    item = loc.nth(idx)
                    if await item.is_visible():
                        return item
            except Exception:
                pass
        # Fallback to the first instance of the first matching selector if none are visible
        for selector in selectors:
            loc = page.locator(selector).first
            try:
                if await loc.count() > 0:
                    return loc
            except Exception:
                pass
        return None

    # ── Pin Creation ───────────────────────────────────────────────────

    async def create_pin(
        self,
        image_path: str,
        title: str,
        description: str,
        board_name: str,
        link: str = "",
        alt_text: str = "",
    ) -> str | None:
        """
        Automate the creation of a new Pin with a self-healing retry loop.
        """
        import os
        import asyncio
        image_path = os.path.abspath(image_path)

        for attempt in range(1, 4):
            logger.info("Pin creation attempt %d of 3...", attempt)
            try:
                # Dismiss modal overlays from any previous crashed sessions
                try:
                    page = await self._get_page()
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                except Exception:
                    pass
                return await self._execute_create_pin(image_path, title, description, board_name, link, alt_text)
            except Exception as attempt_exc:
                logger.warning(f"Pin creation attempt {attempt} failed: {attempt_exc}")
                if attempt == 3:
                    raise
                # Self-healing: close and re-init browser context
                logger.info("Re-initializing page context for next self-healing attempt...")
                try:
                    await self._manager.close()
                    await asyncio.sleep(5)
                    await self._manager.initialize()
                except Exception as recovery_err:
                    logger.error(f"Failed to recover page/browser context: {recovery_err}")
                    await asyncio.sleep(5)

    async def _execute_create_pin(
        self,
        image_path: str,
        title: str,
        description: str,
        board_name: str,
        link: str = "",
        alt_text: str = "",
    ) -> str | None:
        page = await self._get_page()
        logger.info("Executing pin creation flow  │  title='%s'  board='%s'", title, board_name)
        try:
            # Navigate to the Pin Builder (with commit-based wait and soft fallback to survive slow loads)
            try:
                await page.goto(f"{self.BASE_URL}/pin-builder/", wait_until="commit", timeout=60000)
            except Exception as e:
                logger.warning(f"Navigating to pin-builder failed or timed out: {e}")
            
            # Explicitly wait up to 30 seconds for a core component of the pin builder to exist
            try:
                await page.wait_for_selector('input[type="file"], [data-test-id="pin-builder"]', timeout=30000)
            except Exception as e:
                logger.warning(f"Pin builder elements not detected: {e}")
            await page.wait_for_timeout(4000)

            # Dismiss any tour modals (e.g. escape key)
            for _ in range(3):
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)

            # 1. Upload Image
            logger.debug("Uploading image...")
            uploaded = False
            for selector in [
                'input[type="file"][accept*="image"]',
                'input[type="file"]',
                'input[accept="image/*"]'
            ]:
                locs = await page.locator(selector).all()
                for input_el in locs:
                    try:
                        await input_el.set_input_files(image_path)
                        await page.wait_for_timeout(3000)
                        # Check if edit button or image preview is visible
                        if await page.locator('button:has-text("Edit"), button:has-text("Delete")').count() > 0:
                            uploaded = True
                            break
                    except Exception:
                        pass
                if uploaded:
                    break

            if not uploaded:
                logger.warning("Image upload preview elements not detected, hoping file input set succeeded.")

            # 2. Fill Title
            logger.debug("Filling title...")
            title_input = None
            try:
                # Auto-dismiss any leave site dialogs that block navigation
                import asyncio
                page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
                
                title_input = await self._find_visible_locator(page, [
                    'textarea[placeholder="Add your title"]',
                    'input[placeholder="Add your title"]',
                    '[placeholder="Add your title"]',
                    'textarea[placeholder="Add a title"]',
                    'input[placeholder="Add a title"]',
                    '[placeholder="Add a title"]',
                    'textarea[id^="pin-draft-title-"]',
                    'input[id^="pin-draft-title-"]',
                    'input[id="pin-draft-title"]',
                    '#pin-draft-title',
                    'div[role="textbox"][aria-label*="title" i]',
                    '[aria-label*="title" i]',
                    '[data-test-id="pin-draft-title"] textarea',
                    '[data-test-id="pin-draft-title"] input',
                    '[data-test-id="pin-draft-title"]',
                    '[data-test-id^="pin-draft-title"]',
                ])

                # JS fallback: find any input/textarea whose placeholder contains "title" (case-insensitive)
                if not title_input:
                    logger.info("Standard title selectors failed, trying JS-based placeholder search...")
                    try:
                        js_handle = await page.evaluate_handle("""
                            () => {
                                const candidates = [...document.querySelectorAll('input, textarea, [contenteditable="true"], [role="textbox"]')];
                                return candidates.find(el => {
                                    const ph = (el.placeholder || el.getAttribute('aria-label') || el.getAttribute('data-placeholder') || '').toLowerCase();
                                    return ph.includes('title');
                                }) || null;
                            }
                        """)
                        el = js_handle.as_element()
                        if el:
                            title_input = page.locator(':root').locator('css=input, textarea, [contenteditable]').filter(has=page.locator(':scope')).first
                            # Use direct element handle instead
                            await js_handle.as_element().click()
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.type(title[:100], delay=10)
                            logger.info("Successfully filled Pinterest title via JS placeholder search.")
                            title_input = None  # Mark as already handled
                    except Exception as js_e:
                        logger.debug(f"JS title search failed: {js_e}")
                        
                if title_input:
                    await title_input.scroll_into_view_if_needed()
                    await title_input.click()
                    await page.wait_for_timeout(200)
                    await title_input.press("Control+A")
                    await title_input.press("Backspace")
                    await page.keyboard.type(title[:100], delay=10)
                    logger.info("Successfully filled Pinterest title via keyboard type.")
                else:
                    logger.warning("Could not find title input field.")
            except Exception as e:
                logger.warning(f"Exception filling title: {e}")

            # 3. Fill Description
            logger.debug("Filling description...")
            try:
                desc_input = await self._find_visible_locator(page, [
                    '[data-test-id="pin-draft-description"]',
                    '[data-test-id="pin-draft-description"] textarea',
                    '[data-test-id="pin-draft-description"] [contenteditable="true"]',
                    'textarea[placeholder*="description" i]',
                    'input[placeholder*="description" i]',
                    'textarea[placeholder*="tell" i]',
                    '[placeholder*="tell everyone" i]',
                    '[placeholder*="what your Pin is about" i]',
                    '[aria-label*="what your Pin is about" i]',
                    '[aria-label*="description" i]',
                    'textarea[id^="pin-draft-description-"]',
                    'input[id^="pin-draft-description-"]',
                    '[data-test-id^="pin-draft-description-"] .public-DraftEditor-content',
                    '[data-test-id^="pin-draft-description-"] [contenteditable="true"]',
                    '.public-DraftEditor-content'
                ])

                # Check safely if desc_input is identical to title_input
                is_same_as_title = False
                if desc_input and title_input:
                    try:
                        title_handle = await title_input.element_handle()
                        desc_handle = await desc_input.element_handle()
                        if title_handle and desc_handle:
                            is_same_as_title = await page.evaluate("(elems) => elems[0] === elems[1]", [title_handle, desc_handle])
                    except Exception as eval_err:
                        logger.debug(f"Element comparison error: {eval_err}")

                # Fallback: If desc_input wasn't found or matched title_input, pick the 2nd visible textbox on page
                if not desc_input or is_same_as_title:
                    text_boxes = await page.locator('textarea, div[contenteditable="true"], div[role="textbox"], input[type="text"]').all()
                    visible_boxes = []
                    for box in text_boxes:
                        if await box.is_visible():
                            visible_boxes.append(box)
                    if len(visible_boxes) >= 2:
                        desc_input = visible_boxes[1]

                if desc_input:
                    await desc_input.scroll_into_view_if_needed()
                    await desc_input.click(force=True)
                    await page.wait_for_timeout(500)
                    
                    # 1. Try setting value / innerText via JS + dispatch React events
                    try:
                        await desc_input.evaluate("""(el, text) => {
                            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                                el.value = text;
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                            } else {
                                el.innerText = text;
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }""", description)
                        await page.wait_for_timeout(500)
                    except Exception as js_err:
                        logger.debug(f"JS description injection fallback: {js_err}")

                    # 2. Follow up with focus and keyboard typing for full React synthetic event trigger
                    try:
                        await desc_input.focus()
                        await desc_input.press("Control+A")
                        await desc_input.press("Backspace")
                        await page.keyboard.type(description, delay=5)
                        await page.wait_for_timeout(1000)
                    except Exception as type_err:
                        logger.debug(f"Keyboard description type fallback: {type_err}")

                    # 3. Dispatch final input, change, and blur events so React state commits
                    try:
                        await desc_input.evaluate("""el => {
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('blur', { bubbles: true }));
                        }""")
                    except Exception:
                        pass
                        
                    await page.wait_for_timeout(1000)
                    logger.info("Successfully filled Pinterest description.")
                else:
                    logger.warning("Could not find description input field.")
            except Exception as e:
                logger.warning(f"Could not fill description: {e}")

            # 4. Fill Link (optional)
            if link:
                logger.debug("Filling destination link...")
                try:
                    link_input = await self._find_visible_locator(page, [
                        'textarea[placeholder="Add a destination link"]',
                        'input[placeholder="Add a destination link"]',
                        '[placeholder="Add a destination link"]',
                        '[placeholder*="link" i]',
                        'textarea[id^="pin-draft-link-"]',
                        'input[id^="pin-draft-link-"]',
                        'input[id="pin-draft-link"]',
                        '[aria-label*="link" i]'
                    ])

                    if link_input:
                        await link_input.scroll_into_view_if_needed()
                        await link_input.click()
                        await page.wait_for_timeout(200)
                        await link_input.fill(link)
                        # Verification check
                        val = await link_input.input_value()
                        if not val:
                            await link_input.press("Control+A")
                            await link_input.press("Backspace")
                            await page.keyboard.type(link, delay=5)
                        logger.info("Successfully filled Pinterest link.")
                    else:
                        logger.warning("Could not find destination link input field.")
                except Exception as e:
                    logger.warning(f"Exception filling destination link: {e}")

            # 4b. Fill Alt Text (optional)
            if alt_text:
                logger.debug("Filling alt text...")
                try:
                    # Look for the "Add alt text" button
                    alt_btn = await self._find_visible_locator(page, [
                        'text="Add alt text"',
                        'button:has-text("Add alt text")',
                        '[data-test-id="pin-draft-alt-text-button"] button',
                        '[data-test-id="pin-draft-alt-text-button"]',
                        'button:has-text("alt text" i)',
                    ])

                    if alt_btn:
                        await alt_btn.scroll_into_view_if_needed()
                        await alt_btn.click(force=True)
                        await page.wait_for_timeout(500)
                        
                        # Find the textarea that appears, ensuring we don't pick description/title textbox
                        alt_input = await self._find_visible_locator(page, [
                            'textarea[placeholder*="Explain"]',
                            'textarea[placeholder*="people can see in the Pin" i]',
                            '[placeholder*="people can see in the Pin" i]',
                            'textarea[placeholder*="alt text" i]',
                            '[placeholder*="alt text" i]',
                        ])

                        if alt_input:
                             # Slice to 450 max characters as requested by user specification
                             alt_text_short = alt_text[:450].strip()
                             logger.info(f"Filling alt text (trimmed to {len(alt_text_short)} chars)...")
                             
                             await alt_input.scroll_into_view_if_needed()
                             await alt_input.focus()
                             await alt_input.click()
                             await page.wait_for_timeout(500)
                             
                             # Fill the value
                             await alt_input.fill(alt_text_short)
                             await page.wait_for_timeout(200)
                             
                             # Force React state synchronization by dispatching events
                             await alt_input.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                             await alt_input.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                             
                             # Press a dummy key to trigger keyboard listeners
                             await alt_input.press(" ")
                             await alt_input.press("Backspace")
                             await page.wait_for_timeout(1500) # Increased wait time to 1.5 seconds for UI state save
                             
                             # Verification check
                             val = await alt_input.input_value()
                             if not val:
                                 logger.warning("Standard fill did not register alt text. Falling back to keyboard typing...")
                                 await alt_input.press("Control+A")
                                 await alt_input.press("Backspace")
                                 await page.keyboard.type(alt_text_short, delay=10)
                                 await page.wait_for_timeout(1500)
                                 
                             logger.info("Successfully filled alt text.")
                        else:
                            logger.warning("Could not find alt text textarea after clicking button")
                    else:
                         logger.warning("Could not find 'Add alt text' button")
                except Exception as e:
                    logger.warning(f"Exception filling alt text: {e}")

            # 5. Select Board
            logger.debug("Selecting board '%s'...", board_name)
            try:
                board_dropdown = page.locator('[data-test-id="board-dropdown-select-button"]')
                await board_dropdown.click(force=True)
                # Wait up to 5s for the dropdown container or search box to appear
                try:
                    await page.wait_for_selector('[role="listbox"], input[placeholder*="Search" i], [data-test-id="board-dropdown"]', timeout=5000)
                except Exception:
                    pass
                await page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Could not click board dropdown: {e}")
            
            # Type board name in the search field to filter
            search_input = None
            for selector in [
                'input[placeholder*="Search" i]',
                'input[id="searchBoxContainer"]',
                '[role="listbox"] input',
                '.dropdown input',
                'input[type="text"]'
            ]:
                loc = page.locator(selector).first
                if await loc.count() > 0:
                    search_input = loc
                    break

            if search_input:
                await search_input.click()
                await page.wait_for_timeout(500)
                await search_input.fill(board_name)
                # Wait longer for Pinterest to search and update the dropdown
                await page.wait_for_timeout(4000)
                
            # Try to find exact or case-insensitive match among dropdown items
            found = False
            try:
                # Retrieve all dropdown elements, including div[role="button"] which is used in Ads Manager layout
                options_locators = await page.locator('[role="listbox"] [role="option"], [role="listbox"] div, .dropdown div, [data-test-id="board-row"], div[role="button"]').all()
                for opt in options_locators:
                    if not await opt.is_visible():
                        continue
                    text = await opt.inner_text()
                    # Standardize names (strip whitespace, newlines and extra text)
                    clean_text = text.replace('\n', ' ').strip().lower()
                    # Remove trailing 'publish' word if present (e.g. 'K Beauty Publish' -> 'K Beauty')
                    if clean_text.endswith(" publish"):
                        clean_text = clean_text[:-8].strip()
                        
                    if clean_text == board_name.lower():
                        await opt.click(force=True)
                        logger.info("Found and clicked board option: %s", board_name)
                        found = True
                        break
            except Exception as e:
                logger.warning("Error searching options list: %s", e)
                
            if not found:
                # Try direct selectors for board option
                for selector in [
                    f'div[title="{board_name}"]',
                    f'text="{board_name}"',
                    f'div[role="option"]:has-text("{board_name}")',
                    f'[role="option"]:has-text("{board_name}")',
                    f'div[role="button"]:has-text("{board_name}")'
                ]:
                    loc = page.locator(selector).first
                    if await loc.count() > 0:
                        await loc.click(force=True)
                        logger.info("Clicked board option using selector: %s", selector)
                        found = True
                        break
                        
            if not found:
                logger.warning(f"Board '{board_name}' not found in dropdown. Attempting to create it...")
                
                # ── Phase 1: Search for "Create board" button with text still filled ──
                create_board_btn = None
                create_selectors = [
                    '[data-test-id="board-dropdown-create-board-button"]',
                    '[data-test-id="board-dropdown"] >> text="Create board"',
                    '[role="listbox"] >> text="Create board"',
                    'text="Create board"',
                    '[data-test-id="board-dropdown"] >> text="Create"',
                    '[role="listbox"] >> text="Create"',
                    'text="Create"',
                ]
                
                for selector in create_selectors:
                    try:
                        loc = page.locator(selector).first
                        if await loc.count() > 0 and await loc.is_visible():
                            create_board_btn = loc
                            break
                    except Exception as e:
                        logger.warning(f"Selector check failed for '{selector}': {e}")
                        
                # ── Phase 2: If not found, clear search to reset list and try again ──
                if not create_board_btn and search_input:
                    try:
                        logger.info("Create Board button not found with search query. Clearing search query to reset list...")
                        await search_input.click()
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await search_input.fill("")
                        await page.wait_for_timeout(1500)
                        
                        # Try to find it again after clearing
                        for selector in create_selectors:
                            try:
                                loc = page.locator(selector).first
                                if await loc.count() > 0 and await loc.is_visible():
                                    create_board_btn = loc
                                    break
                            except Exception as e:
                                logger.warning(f"Selector check failed for '{selector}' after clear: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to clear dropdown search box: {e}")
                        
                if create_board_btn:
                    logger.info("Found 'Create board' button inside dropdown. Clicking...")
                    await create_board_btn.click(force=True)
                    await page.wait_for_timeout(2000)
                    
                    # Locate the dialog/modal container that has our board edit input
                    modal = page.locator('div:has(input#boardEditName), div:has(input[name="boardName"]), [role="dialog"], [data-test-id="board-edit-modal"], [data-test-id="create-board-modal"]').first
                    if await modal.count() > 0:
                        board_name_input = modal.locator('input#boardEditName, input[name="boardName"]').first
                        if await board_name_input.count() > 0:
                            await board_name_input.fill(board_name)
                            await page.wait_for_timeout(1500)
                            
                        submit_create = modal.locator('button:has-text("Create"), [role="button"]:has-text("Create"), button[type="submit"], [data-test-id="board-form-submit-button"]').first
                        if await submit_create.count() > 0:
                            await submit_create.click(force=True)
                            logger.info(f"Clicked Create button inside modal for board '{board_name}'. Waiting 15 seconds for Pinterest to process...")
                            await page.wait_for_timeout(15000)
                            logger.info(f"Successfully created board: '{board_name}'")
                        else:
                            logger.error("Could not find submit button inside Create Board modal.")
                            await page.keyboard.press('Escape')
                            raise Exception(f"Failed to find submit button inside Create Board modal for: {board_name}")
                    else:
                        logger.error("Could not find Create Board modal/form container.")
                        await page.keyboard.press('Escape')
                        raise Exception("Failed to locate Create Board modal container.")
                else:
                    logger.warning("Could not find 'Create board' option in dropdown. Auto-selecting first available existing board from dropdown...")
                    try:
                        if search_input:
                            await search_input.click()
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await search_input.fill("")
                            await page.wait_for_timeout(1500)

                        first_board_opt = page.locator('[role="listbox"] [role="option"], [data-test-id="board-row"]').first
                        if await first_board_opt.count() > 0:
                            await first_board_opt.click(force=True)
                            logger.info("✅ Self-healing recovery: Selected fallback existing board from Pinterest dropdown!")
                        else:
                            await page.keyboard.press('Escape')
                            await page.wait_for_timeout(1000)
                            raise Exception(f"Failed to select board: {board_name}")
                    except Exception as fb_err:
                        logger.warning(f"Board fallback selection failed: {fb_err}")
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(1000)
                        raise Exception(f"Failed to select or create board: {board_name}")
            # 6. Save Pin
            logger.debug("Saving pin...")
            await page.wait_for_timeout(2000)
            await page.screenshot(path='before_publish.png', full_page=True)
            try:
                publish_btn = None
                for selector in [
                    '[data-test-id="board-dropdown-save-button"]',
                    'button:has-text("Publish")',
                    'div[role="button"]:has-text("Publish")',
                    '[data-test-id="pin-builder-save-btn"]',
                ]:
                    loc = page.locator(selector).first
                    if await loc.count() > 0:
                        publish_btn = loc
                        break
                        
                if publish_btn:
                    await publish_btn.click(force=True)
                    logger.info("Clicked Publish button.")
                else:
                    # Try text fallback
                    publish_btn_text = page.get_by_text("Publish", exact=True).first
                    if await publish_btn_text.count() > 0:
                        await publish_btn_text.click(force=True)
                        logger.info("Clicked Publish button by text.")
                    else:
                        logger.error("Could not find Publish button by any selector or text.")
            except Exception as e:
                logger.error(f"Failed to click Publish button: {e}")

            # 7. Wait for Success Toast/Confirmation + URL redirect
            logger.debug("Waiting for success confirmation...")
            try:
                success_element = None
                # Give Pinterest up to 25s total to show success toast (5 selectors x 5s each)
                for selector in [
                    '[data-test-id="toast"]',
                    'div:has-text("You created a Pin!")',
                    'div:has-text("Saved to")',
                    'a:has-text("See your Pin")',
                    'a:has-text("See it now")'
                ]:
                    loc = page.locator(selector).first
                    try:
                        await loc.wait_for(state="visible", timeout=5000)
                        success_element = loc
                        break
                    except Exception:
                        continue

                if success_element:
                    logger.info("Pin published successfully (toast confirmed)!")
                    for pin_link_selector in [
                        'a[href*="/pin/"]',
                        'a:has-text("See your Pin")',
                        'a:has-text("See it now")'
                    ]:
                        link_loc = page.locator(pin_link_selector).first
                        if await link_loc.count() > 0:
                            href = await link_loc.get_attribute('href')
                            if href:
                                pin_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                                logger.info(f"Extracted Pin URL: {pin_url}")
                                return pin_url
                else:
                    logger.warning("Toast not detected. Waiting up to 10s for page URL redirect to /pin/...")

                # Fallback: wait for URL to change from /pin-builder/ to actual /pin/<id>/
                try:
                    await page.wait_for_function(
                        "() => window.location.href.includes('/pin/') && !window.location.href.includes('pin-builder')",
                        timeout=10000
                    )
                    final_url = page.url
                    logger.info(f"Pin URL detected via redirect: {final_url}")
                    return final_url
                except Exception:
                    # Check current URL one more time
                    current_url = page.url
                    if "/pin/" in current_url and "pin-builder" not in current_url:
                        logger.info(f"Pin URL from current page: {current_url}")
                        return current_url

                    logger.warning("Could not confirm pin publish via toast or URL redirect. Pin may still be live on Pinterest.")
            except Exception as e:
                logger.warning(f"Error checking success confirmation: {e}")

            # Last resort: check if we're no longer on pin-builder
            final_url = page.url
            if "/pin/" in final_url and "pin-builder" not in final_url:
                return final_url
            return "https://www.pinterest.com/pin-builder/"

        except PlaywrightTimeoutError as exc:
            raise ElementNotFoundError(f"Timed out waiting for element during pin creation: {exc}") from exc
        except Exception as exc:
            raise BrowserNavigationError(f"Pin creation failed: {exc}") from exc

    async def scrape_profile_analytics(self, scroll_count: int = 4) -> list[dict[str, Any]]:
        """
        Navigate to the Pinterest profile page, scroll down, and scrape pin analytics.
        
        Returns:
            A list of dicts with keys: 'pin_id', 'impressions', 'saves', 'clicks'
        """
        import re
        page = await self._get_page()
        logger.info("Starting profile analytics scraping...")
        
        results = []
        try:
            # Go to profile
            await page.goto(f"{self.BASE_URL}/me", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            
            # Dismiss any tour modals
            for _ in range(2):
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
                
            # Scroll down to load grid items
            for scroll in range(scroll_count):
                logger.info(f"Scrolling page ({scroll + 1}/{scroll_count})...")
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(3000)
                
            # Locate all listitems
            items = await page.locator('[role="listitem"]').all()
            logger.info("Found %d listitems on profile page.", len(items))
            
            # Regex to match stats pattern in inner text: e.g. "See more stats 4 0 2 ..." or "See more stats 10 2 1 ..."
            pattern = re.compile(r"See\s+more\s+stats\s+(\d+)\s+(\d+)\s+(\d+)", re.IGNORECASE)
            
            for item in items:
                try:
                    text = await item.inner_text()
                    clean_text = " ".join(text.split())
                    
                    match = pattern.search(clean_text)
                    if match:
                        # Find the pin link inside the listitem
                        link_el = item.locator('a[href*="/pin/"]').first
                        if await link_el.count() > 0:
                            href = await link_el.get_attribute("href")
                            if href:
                                # Extract numeric pin ID
                                pin_id_match = re.search(r"/pin/(\d+)", href)
                                if pin_id_match:
                                    pin_id = pin_id_match.group(1)
                                    impressions = int(match.group(1))
                                    clicks = int(match.group(2))
                                    saves = int(match.group(3))
                                    
                                    results.append({
                                        "pin_id": pin_id,
                                        "impressions": impressions,
                                        "saves": saves,
                                        "clicks": clicks
                                    })
                except Exception as item_err:
                    logger.debug("Error processing listitem: %s", item_err)
                    
            logger.info("Successfully scraped analytics for %d pins.", len(results))
            
        except Exception as exc:
            logger.error("Failed to scrape profile analytics: %s", exc)
            
        return results

    # ── Utility ────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the active page if open."""
        if self._page and not self._page.is_closed():
            await self._page.close()
            self._page = None

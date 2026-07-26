"""
Stealth — Anti-bot evasion techniques for Playwright.
======================================================

Pinterest uses advanced bot detection. This module provides techniques
to make the Playwright browser appear more human-like, such as:
    • Rotating realistic User-Agents
    • Modifying navigator properties (webdriver flag)
    • Randomizing viewport sizes slightly
    • Emulating human-like delays

Usage::

    from browser.stealth import apply_stealth, get_random_user_agent
    
    # ... during context creation
    context = await browser.new_context(user_agent=get_random_user_agent())
    await apply_stealth(context)
"""

from __future__ import annotations

import logging
import random
from typing import Any

from playwright.async_api import BrowserContext, Page

logger = logging.getLogger("pinterest_agent.browser.stealth")


# A list of modern, realistic Chrome User-Agents matching Windows Chromium engine
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    """Return a random, realistic User-Agent string."""
    ua = random.choice(USER_AGENTS)
    logger.debug("Selected User-Agent  │  ua=%s", ua[:50] + "...")
    return ua


async def apply_stealth(context_or_page: BrowserContext | Page) -> None:
    """
    Apply anti-bot evasion scripts to a context or page.

    This injects JavaScript that masks typical WebDriver signals cleanly
    without triggering security flags in Google OAuth.
    """
    stealth_script = """
        // 1. Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });

        // 2. Languages fallback
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // 3. Mock window.chrome
        if (!window.chrome) {
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        }

        // 4. Fix permissions query for notifications
        if (window.navigator.permissions) {
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        }
    """
    
    await context_or_page.add_init_script(stealth_script)
    logger.info("Stealth evasion scripts applied.")


def get_randomized_viewport(base_width: int = 1280, base_height: int = 800) -> dict[str, int]:
    """
    Generate a slightly randomized viewport size.
    
    Bot detectors sometimes flag exact standard dimensions.
    This adds a small jitter to make it look like a manually resized window.

    Args:
        base_width:  Target width.
        base_height: Target height.

    Returns:
        Dict with 'width' and 'height'.
    """
    # Jitter between -20 and +20 pixels
    w_jitter = random.randint(-20, 20)
    h_jitter = random.randint(-20, 20)
    
    width = max(800, base_width + w_jitter)
    height = max(600, base_height + h_jitter)
    
    logger.debug("Randomized viewport  │  %dx%d", width, height)
    return {"width": width, "height": height}

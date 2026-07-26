"""
Amazon Client — Playwright-based scraper and affiliate link generator.
========================================================================

Extracts product details (title, description, high-res images) from
Amazon URLs and generates Affiliate tags automatically.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from browser.browser_manager import BrowserManager

logger = logging.getLogger("pinterest_agent.browser.amazon")


@dataclass
class AmazonProduct:
    """Extracted data from an Amazon product page."""
    title: str
    description: str
    image_url: str
    affiliate_url: str
    rating: float = 0.0
    review_count: int = 0
    price: str = ""


class AmazonClient:
    """
    Automates interaction with Amazon to fetch product details
    and generate affiliate links.
    """

    def __init__(self, manager: BrowserManager, affiliate_tag: str = "yourtag-20"):
        self.manager = manager
        self.affiliate_tag = affiliate_tag
        logger.info("AmazonClient initialized  │  tag=%s", self.affiliate_tag)

    @staticmethod
    def parse_amazon_rating(text: str) -> float:
        """Parse rating like '4.6 out of 5 stars' or '4.6' into float."""
        import re
        if not text:
            return 0.0
        match = re.search(r'([0-4]\.\d|5\.0|[1-5])', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0

    @staticmethod
    def parse_amazon_review_count(text: str) -> int:
        """Parse review count like '15,482 ratings' or '1,250' into int."""
        import re
        if not text:
            return 0
        clean_text = text.replace(',', '').replace('.', '')
        match = re.search(r'(\d+)', clean_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    @staticmethod
    def add_affiliate_tag(url: str, tag: str) -> str:
        """
        Appends or replaces the Amazon affiliate tag in a given URL.
        Converts product URLs into clean https://www.amazon.com/dp/ASIN?tag=TAG format.
        """
        if not url:
            return ""
        
        import re
        match = re.search(r'/(?:dp|gp/product|gp/video|d)/([A-Z0-9]{10})', url, re.IGNORECASE)
        if match:
            asin = match.group(1).upper()
            return f"https://www.amazon.com/dp/{asin}?tag={tag}"
        
        try:
            parsed = urlparse(url)
            query_dict = parse_qs(parsed.query)
            query_dict["tag"] = [tag]
            new_query = urlencode(query_dict, doseq=True)
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        except Exception:
            return url

    async def search_products(
        self, 
        keyword: str, 
        min_rating: float = 4.3, 
        min_reviews: int = 1000
    ) -> str | None:
        """
        Search Amazon Beauty for a keyword and return the URL of the first organic product
        that satisfies Quality Shield criteria (Rating >= min_rating, Reviews >= min_reviews).
        
        Args:
            keyword: The search term (e.g. "latest beauty products").
            min_rating: Minimum star rating (default 4.3).
            min_reviews: Minimum review count (default 1000).
            
        Returns:
            The raw Amazon product URL, or None if no products found.
        """
        logger.info("Searching Amazon for: '%s' (Quality Shield: Rating>=%.1f★, Reviews>=%d)...", keyword, min_rating, min_reviews)
        context = self.manager.context
        page = await context.new_page()
        
        try:
            # Navigate to Amazon Beauty search specifically
            search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&i=beauty"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            logger.info("Simulating proper human research on Amazon Beauty Search...")
            
            # Slowly scroll down to view products
            for _ in range(6):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(1500)
                
            # Slowly scroll back up
            for _ in range(2):
                await page.mouse.wheel(0, -800)
                await page.wait_for_timeout(1500)
            
            book_terms = ["book", "paperback", "hardcover", "kindle", "edition", "novel", "handbook", "manual", "usmle", "study guide", "textbook", "audiobook", "guide"]
            
            # Locate search result cards
            result_cards = page.locator('div[data-component-type="s-search-result"]')
            card_count = await result_cards.count()
            logger.info("Found %d search result cards on Amazon.", card_count)
            
            candidates = []
            
            for i in range(min(card_count, 20)):
                card = result_cards.nth(i)
                link_loc = card.locator('a[href*="/dp/"]').first
                if await link_loc.count() == 0:
                    continue
                    
                href = await link_loc.get_attribute("href")
                if not href or "/dp/" not in href:
                    continue
                    
                link_text = (await link_loc.inner_text()).lower()
                href_lower = href.lower()
                
                # Check if URL or link text indicates a book
                if any(bt in href_lower or bt in link_text for bt in book_terms):
                    logger.warning("Filtering out non-beauty/book product candidate: %s", href[:60])
                    continue
                    
                full_url = href if href.startswith("http") else "https://www.amazon.com" + href
                
                # Extract Rating
                rating = 0.0
                rating_loc = card.locator('i[class*="a-icon-star"], span[aria-label*="out of 5 stars"], span.a-icon-alt').first
                if await rating_loc.count() > 0:
                    r_text = await rating_loc.get_attribute("aria-label") or await rating_loc.inner_text() or ""
                    rating = self.parse_amazon_rating(r_text)
                    
                # Extract Review Count
                reviews = 0
                review_loc = card.locator('span[aria-label*="ratings"], span[aria-label*="reviews"], a[href*="#customerReviews"] span, span.s-underline-text').first
                if await review_loc.count() > 0:
                    rev_text = await review_loc.get_attribute("aria-label") or await review_loc.inner_text() or ""
                    reviews = self.parse_amazon_review_count(rev_text)
                    
                logger.info("Candidate #%d: Rating=%.1f★, Reviews=%d │ URL: %s", i+1, rating, reviews, full_url[:60])
                
                # Check Quality Shield criteria
                if rating >= min_rating and reviews >= min_reviews:
                    logger.info("🛡️ QUALITY SHIELD PASSED! Candidate #%d: Rating %.1f★, Reviews %d", i+1, rating, reviews)
                    candidates.append((rating, reviews, full_url))
                elif rating >= 4.0 and reviews >= 100:
                    candidates.append((rating, reviews, full_url))
                    
            if candidates:
                # Sort descending by review count and star rating to select the #1 Bestseller Hero Product
                candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
                best_rating, best_reviews, best_url = candidates[0]
                logger.info("🏆 SELECTED #1 HERO BEAUTY PRODUCT: Rating %.1f★, Reviews %d │ %s", best_rating, best_reviews, best_url[:60])
                return best_url

            # Final Fallback
            product_links = page.locator('a[href*="/dp/"]')
            count = await product_links.count()
            for i in range(min(count, 15)):
                link_loc = product_links.nth(i)
                href = await link_loc.get_attribute("href")
                if href and "/dp/" in href:
                    if not any(bt in href.lower() for bt in book_terms):
                        full_url = href if href.startswith("http") else "https://www.amazon.com" + href
                        return full_url
                        
            logger.warning("No valid beauty products found for keyword: %s", keyword)
            return None
            
        except Exception as exc:
            logger.error("Failed to search Amazon: %s", exc)
            return None
            
        finally:
            await page.close()

    async def fetch_product_details(self, url: str) -> AmazonProduct:
        """
        Navigate to the Amazon product page and extract its metadata.
        
        Args:
            url: The raw Amazon product URL.
            
        Returns:
            AmazonProduct dataclass containing title, desc, image, rating, review_count, and tagged URL.
        """
        logger.info("Fetching product details from: %s", url)
        context = self.manager.context
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 1. Extract Title
            title_loc = page.locator("#productTitle").first
            title = await title_loc.inner_text() if await title_loc.count() > 0 else "Unknown Product"
            title = title.strip()
            
            # Anti-Book Check on extracted Amazon product title
            book_terms = ["paperback", "hardcover", "kindle edition", "spiral-bound", "audiobook", "handbook", "manual", "usmle", "study guide", "textbook", "guidebook", "navigation handbook"]
            title_lower = title.lower()
            if any(bt in title_lower for bt in book_terms):
                logger.error("Rejecting product '%s' - detected as a book/manual/guide.", title)
                raise ValueError(f"Product '{title}' is a book/literature item, not a beauty product.")
            
            # 2. Extract Description (Feature Bullets)
            desc_loc = page.locator("#feature-bullets li span.a-list-item")
            bullets = await desc_loc.all_inner_texts()
            description = "\n".join(b.strip() for b in bullets if b.strip())
            if not description:
                description = f"Check out this amazing {title} on Amazon!"
                
            # 3. Extract High-Res Image
            image_url = ""
            try:
                img_loc = page.locator("#landingImage, #imgBlkFront, #main-image").first
                if await img_loc.count() > 0:
                    image_url = await img_loc.get_attribute("src", timeout=2000) or ""
                    hires = await img_loc.get_attribute("data-old-hires", timeout=1000)
                    if hires:
                        image_url = hires
            except Exception as e:
                logger.warning(f"Could not extract Amazon image: {e}")
                
            # 4. Generate Affiliate Link
            affiliate_url = self.add_affiliate_tag(page.url, self.affiliate_tag)
            
            # 5. Extract Rating & Review Count
            rating = 0.0
            try:
                pop_loc = page.locator("#acrPopover, i.a-icon-star, span.a-icon-alt").first
                if await pop_loc.count() > 0:
                    pop_text = await pop_loc.get_attribute("title") or await pop_loc.get_attribute("aria-label") or await pop_loc.inner_text() or ""
                    rating = self.parse_amazon_rating(pop_text)
            except Exception as e:
                logger.debug(f"Could not extract rating: {e}")
                
            review_count = 0
            try:
                rev_loc = page.locator("#acrCustomerReviewText, span[data-hook='total-review-count']").first
                if await rev_loc.count() > 0:
                    rev_text = await rev_loc.inner_text() or ""
                    review_count = self.parse_amazon_review_count(rev_text)
            except Exception as e:
                logger.debug(f"Could not extract review count: {e}")
                
            # 6. Extract Actual Real Price
            price = ""
            try:
                whole_loc = page.locator("span.a-price-whole").first
                frac_loc = page.locator("span.a-price-fraction").first
                if await whole_loc.count() > 0 and await frac_loc.count() > 0:
                    w = (await whole_loc.inner_text()).strip().replace(".", "").replace(",", "")
                    f = (await frac_loc.inner_text()).strip()
                    if w.isdigit() and f.isdigit():
                        price = f"${w}.{f}"

                if not price:
                    price_loc = page.locator("span.a-price span.a-offscreen, #priceblock_ourprice, #priceblock_dealprice, #corePrice_feature_div span.a-offscreen").first
                    if await price_loc.count() > 0:
                        raw_p = await price_loc.inner_text() or await price_loc.get_attribute("textContent") or ""
                        raw_p = raw_p.strip().replace("\n", "").replace(" ", "")
                        
                        import re
                        m1 = re.search(r'\$?(\d+)\.(\d{2})', raw_p)
                        if m1:
                            price = f"${m1.group(1)}.{m1.group(2)}"
                        else:
                            m2 = re.search(r'\$?(\d+)', raw_p)
                            if m2:
                                num = m2.group(1)
                                if len(num) >= 3:
                                    price = f"${num[:-2]}.{num[-2:]}"
                                else:
                                    price = f"${num}"
            except Exception as e:
                logger.debug(f"Could not extract price: {e}")

            logger.info("Successfully extracted Amazon product  │  title=%s  price=%s  rating=%.1f★  reviews=%d", title[:30], price or "N/A", rating, review_count)
            
            return AmazonProduct(
                title=title,
                description=description,
                image_url=image_url,
                affiliate_url=affiliate_url,
                rating=rating,
                review_count=review_count,
                price=price
            )
            
        except Exception as exc:
            logger.error("Failed to fetch Amazon product: %s", exc)
            raise
            
        finally:
            await page.close()

    async def get_us_beauty_best_sellers(self) -> str:
        """
        Scrape top products from Amazon US Beauty Best Sellers.
        Returns a comma-separated string of product titles.
        """
        logger.info("Fetching Amazon US Beauty Best Sellers...")
        context = self.manager.context
        page = await context.new_page()
        
        try:
            await page.goto("https://www.amazon.com/Best-Sellers-Beauty/zgbs/beauty", wait_until="domcontentloaded", timeout=60000)
            logger.info("Simulating proper human research on Amazon Best Sellers...")
            
            # Wait for page to settle
            await page.wait_for_timeout(5000)
            
            # Slowly scroll down through the top products
            for _ in range(12):
                await page.mouse.wheel(0, 700)
                await page.wait_for_timeout(3000)
                
            # Scroll back up a bit
            for _ in range(3):
                await page.mouse.wheel(0, -1000)
                await page.wait_for_timeout(2000)
            
            texts = await page.locator('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, div.p13n-sc-truncate-desktop-type2, span._cDEzb_p13n-sc-css-line-clamp-2_EWgCb, div[class*="line-clamp"]').all_inner_texts()
            
            if not texts:
                texts = await page.locator('div#gridItemRoot a > span > div').all_inner_texts()
                
            valid_texts = set()
            for t in texts:
                t = t.strip()
                if t and len(t) > 5 and "Amazon" not in t:
                    valid_texts.add(t)
                    
            best_sellers = list(valid_texts)[:30]
            logger.info("Found %d products from Amazon Best Sellers.", len(best_sellers))
            return ", ".join(best_sellers)
            
        except Exception as exc:
            logger.error("Failed to fetch Amazon Best Sellers: %s", exc)
            return ""
            
        finally:
            await page.close()

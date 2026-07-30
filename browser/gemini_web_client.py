"""
Gemini Web Client — Playwright automation for gemini.google.com
================================================================

Automates the Gemini Web UI to avoid needing an API key.
Requires the user to log in to Google once manually in the browser.
The session is then saved and reused.
"""

from __future__ import annotations

import json
import logging
import asyncio
from dataclasses import dataclass

from browser.browser_manager import BrowserManager

logger = logging.getLogger("pinterest_agent.browser.gemini")


@dataclass
class PinterestSEOData:
    """The generated SEO data for a Pinterest Pin."""
    title: str
    description: str
    alt_text: str
    tags: str
    board: str
    image_headline: str = ""
    curiosity_hook: str = ""


class GeminiWebClient:
    """
    Automates the gemini.google.com web interface for free AI processing.
    """

    def __init__(self, manager: BrowserManager):
        self.manager = manager
        logger.info("GeminiWebClient initialized (No API required).")

    async def _send_prompt(self, prompt: str, image_path: str | None = None) -> str:
        """
        Navigate to Gemini, enter the prompt and optional image, and scrape the response.
        """
        logger.info("Opening Gemini Web UI...")
        context = self.manager.context
        page = await context.new_page()
        
        try:
            # Note: User must have logged into Google previously, and session saved by BrowserManager.
            await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
            
            # Check if login is required (if we don't see the chat input)
            try:
                await page.wait_for_selector('rich-textarea, div[contenteditable="true"], [aria-label*="prompt"]', timeout=15000)
            except Exception:
                logger.error("Could not find Gemini chat input. Please run login_gemini.py to log in to Google!")
                return ""

            # Detect Google login state (unauthenticated sessions have image upload disabled by Google)
            signin_btn = page.locator('button:has-text("Sign in"), a[href*="accounts.google.com"], [aria-label="Sign in"]').first
            is_signed_in = await signin_btn.count() == 0
            if not is_signed_in and image_path:
                logger.info("Google Sign-In prompt detected. Image upload to Gemini skipped (requires Google login). Text SEO will generate normally, and high-res Amazon editorial pin will be used.")

            # 1. Upload Image (if provided and signed in)
            if image_path and is_signed_in:
                logger.debug("Uploading image to Gemini...")
                uploaded = False
                try:
                    # Strategy 1: Direct set_input_files on input[type="file"] if present
                    file_input = page.locator('input[type="file"]').first
                    if await file_input.count() > 0:
                        try:
                            await file_input.set_input_files(image_path)
                            uploaded = True
                            logger.info("Uploaded image via direct input[type='file'].")
                        except Exception as e_dir:
                            logger.debug(f"Direct input file set failed: {e_dir}")

                    # Strategy 2: Click + button (Upload & tools), then target active uploader button
                    if not uploaded:
                        add_btn = page.locator('button[aria-label="Upload & tools"], button[aria-label*="Upload image"], button[aria-label*="Add file"], button[data-test-id*="uploader"]').first
                        if await add_btn.count() > 0:
                            await add_btn.click(timeout=3000)
                            await page.wait_for_timeout(500)

                            file_input_after = page.locator('input[type="file"]').first
                            if await file_input_after.count() > 0:
                                try:
                                    await file_input_after.set_input_files(image_path)
                                    uploaded = True
                                    logger.info("Uploaded image via input[type='file'] after clicking + button.")
                                except Exception as e_after:
                                    logger.debug(f"Input file set after + button click failed: {e_after}")

                            if not uploaded:
                                # Target active enabled button 'uploader-images-files-button-advanced'
                                upload_btn = page.locator('[data-test-id="uploader-images-files-button-advanced"], [data-test-id*="uploader-images-files"], [role="menuitem"]:not([disabled]):has-text("Upload files"), [role="menuitem"]:has-text("Upload files")').first
                                if await upload_btn.count() > 0:
                                    try:
                                        inner_input = upload_btn.locator('input[type="file"]')
                                        if await inner_input.count() > 0:
                                            await inner_input.first.set_input_files(image_path)
                                            uploaded = True
                                            logger.info("Uploaded image via inner input[type='file'] inside uploader button.")
                                        else:
                                            async with page.expect_file_chooser(timeout=4000) as fc_info:
                                                await upload_btn.click(timeout=3000)
                                            file_chooser = await fc_info.value
                                            await file_chooser.set_files(image_path)
                                            uploaded = True
                                            logger.info("Uploaded image via file chooser event on advanced uploader button.")
                                    except Exception as e_fc:
                                        logger.warning(f"File chooser upload attempt failed: {e_fc}")

                    if uploaded:
                        # Wait for image thumbnail preview to appear in the compose box
                        try:
                            await page.wait_for_selector('thumbnail-preview img, [class*="thumbnail" i], [class*="preview" i], [aria-label*="image" i], mat-chip-row', timeout=8000)
                        except Exception:
                            logger.warning("Timed out waiting for image thumbnail preview to appear, proceeding anyway.")
                    else:
                        logger.warning("Could not upload image to Gemini with available strategies.")
                except Exception as e:
                    logger.warning(f"Failed to upload image to Gemini: {e}")

            # 2. Type Prompt
            logger.debug("Typing prompt...")
            chat_locator = page.locator('rich-textarea, div[contenteditable="true"], [aria-label*="prompt"]').first
            await chat_locator.click()
            await page.wait_for_timeout(500)
            await page.keyboard.insert_text(prompt)
            
            # 3. Send Message
            # Wait a brief moment to ensure the send button becomes active
            await page.wait_for_timeout(1000)
            send_button = page.locator('button[aria-label*="Send"], button[aria-label*="Submit"]')
            if await send_button.count() > 0:
                await send_button.first.click()
            else:
                await chat_locator.press("Enter")
                
            # 4. Wait for response to generate
            logger.info("Waiting for Gemini to write response...")
            # Gemini typically shows a loading indicator (stop generating button)
            # We wait for it to appear, then wait for it to disappear
            try:
                await page.wait_for_selector('button[aria-label*="Stop generating"]', timeout=10000)
                await page.locator('button[aria-label*="Stop generating"]').wait_for(state="hidden", timeout=60000)
            except Exception:
                # If it doesn't appear, just wait a fixed amount of time
                await page.wait_for_timeout(15000)
                
            # 5. Scrape the latest response
            # Gemini responses are typically in a message-content block. We get the last one.
            response_blocks = page.locator('message-content')
            count = await response_blocks.count()
            
            if count > 0:
                latest_response = await response_blocks.nth(count - 1).inner_text()
                return latest_response.strip()
            else:
                logger.error("Could not find response block in Gemini UI.")
                return ""
                
        except Exception as exc:
            logger.error("Gemini Web Automation failed: %s", exc)
            return ""
            
        finally:
            await page.close()

    async def analyze_ui_for_selector(self, screenshot_path: str, failed_selector: str, context: str) -> str:
        """
        Vision-based self-healing core.
        Uploads a screenshot of a broken page to Gemini and asks for the correct CSS selector.
        """
        prompt = f"""
You are an expert Automation QA Engineer and Playwright/CSS expert.
The automated agent failed to find a UI element on the screen using the CSS selector '{failed_selector}'.
Context of what we were trying to do: {context}

Look at the attached screenshot of the current UI. Identify the correct element and provide a robust CSS selector to interact with it.
If it's an email field, password field, or login button, provide the most robust identifier (e.g., `#password`, `input[type="password"]`, `button[type="submit"]`).

CRITICAL RULES:
1. Return ONLY the CSS selector string. Do not include any markdown, explanation, or code blocks.
2. The response must be a valid Playwright CSS selector.
3. If you cannot identify the element, return exactly: "ERROR: Not found"
"""
        response_text = await self._send_prompt(prompt, image_path=screenshot_path)
        
        # Clean up response in case it added markdown
        clean_selector = response_text.replace("```css", "").replace("```", "").strip()
        # If it returned a long explanation despite rules, fallback
        if len(clean_selector) > 100 or " " in clean_selector and not any(c in clean_selector for c in ['[', '>', '.', '#']):
            logger.error(f"Gemini returned invalid selector format: {clean_selector}")
            return "ERROR: Invalid response"
            
        logger.info(f"Vision Self-Healing returned new selector: {clean_selector}")
        return clean_selector

    async def generate_image_and_seo(
        self, 
        product_title: str, 
        product_desc: str, 
        image_path: str | None = None, 
        product_price: str = "",
        product_rating: float = 0.0,
        product_reviews: int = 0
    ) -> tuple[str | None, PinterestSEOData]:
        """
        Ask Gemini to generate an aesthetic Pinterest image of the product AND the SEO text in one prompt.
        Requires the user to be logged in to Google.
        Returns:
         Tuple of (downloaded_image_url, PinterestSEOData).
        """
        allowed_boards = [
            # High-Converting Long-Tail K-Beauty & Skincare Boards
            "Korean Sunscreens That Leave Zero White Cast",
            "K-Beauty Serums That Actually Work",
            "Korean Glass Skin Cleansers USA 2026",
            "Bio-Collagen Glass Skin Overnight Masks",
            "Medicube Pore Pads & PDRN Peptide Serums",
            "Skin Barrier Repair & Ceramide Creams",
            "Non-Comedogenic Moisturizers For Acne Prone Skin",
            "Dark Circle Eye Creams & Caffeine Serums",
            "Retinol & Bakuchiol Anti-Aging Holy Grails",
            "Vitamin C & Niacinamide Brightening Serums",
            "Korean Centella & Cica Soothing Skincare",
            "Hydrating Facial Mists & Essence Toners",
            "K-Beauty Moisture Secrets",
            "Dewy Moisturizers & Daily SPF",
            "Overnight Acne & Pimple Patches",
            "Dark Spot Correctors & Brightening",
            "Clean Beauty Skincare Routines",
            "Back-To-School 5-Minute Skincare & Beauty",
            # High-CTR Lip Care & Dupes Boards
            "Dior Lip Oil $8 Amazon Dupes",
            "Summer Fridays & Rhode Lip Treatments",
            "Dark Berry & Oxblood Lip Stains 2026",
            "Laneige Overnight Lip Mask Flavors",
            "Coquette Soft Pink Lip Balms & Glosses",
            "Viral Lip Oils & Tints",
            "Sephora Viral Beauty Dupes",
            # Sweat-Proof Makeup & Complexion Boards
            "ONE/SIZE Waterproof Setting Sprays & Primers",
            "TirTir Cushion Foundation & Cloud Skin",
            "Rare Beauty Liquid Blush & Bronzer Glow",
            "Charlotte Tilbury Flawless Filter Amazon Dupes",
            # UK Target Boards (Boots, Cult Beauty & Amazon UK)
            "Boots & Cult Beauty UK Viral Finds",
            "Charlotte Tilbury & Refy UK Dupes",
            "The Ordinary & Weleda Skin Food Secrets",
            "La Roche-Posay Anthelios SPF UK",
            "UK High Street Beauty Essentials 2026",
            "London Clean Girl Aesthetic Beauty",
            "Color Wow & Anti-Frizz UK Hair Care",
            "UK Drugstore Beauty Gems Under £15",
            # Canada Target Boards (Shoppers Drug Mart, Sephora CA & Amazon CA)
            "Shoppers Drug Mart & Sephora CA Beauty Finds",
            "The Ordinary & First Aid Beauty Canada",
            "Summer Fridays & Nudestix Canada Favorites",
            "Canada Winter Skincare & Hydration Secrets",
            "Amazon Canada Viral Beauty Under $25",
            "Clean Girl Concealer & Eye Brighteners",
            "Soft Glam Cream Bronzer & Liquid Contour",
            "Tubing Mascara & Eyelash Growth Serums",
            "Clean Girl Aesthetic Makeup",
            "Full Coverage Foundation & Concealer",
            "Drugstore Beauty Gems Under $15",
            # Hair Care, Tools & Blowout Boards
            "Shark FlexStyle Airwrap Dupes & Styling",
            "Rosemary Hair Oil & Scalp Massager Tools",
            "Heatless Silk Curlers & Overnight Waves",
            "Scalp Scrub & Clarifying Detox Shampoos",
            "Bond Repair Masks For Bleached Hair",
            "Hair Tools & Heatless Styling",
            "Hair Growth Oils & Scalp Density",
            "Anti-Frizz & Bond Repair Hair Care 2026",
            "90s Blowout & Hair Care Secrets",
            # Body Care, Sunless Tanners & Fragrance
            "St. Tropez & Jergens Sunless Tanners",
            "Body Wash Shower Gels USA 2026",
            "Sol De Janeiro Body Sprays & Scent Dupes",
            "Exfoliating Body Scrubs & Strawberry Skin Fix",
            "Gourmand Vanilla & Pistachio Body Lotions",
            "Arabian Perfume Oils & Vanilla Body Mists",
            "Aesthetic Vanilla Body Routine",
            "Viral Perfumes & Body Mists",
            "KP & Strawberry Legs Treatments",
            "Self Care Bath & Body Spa Essentials",
            # Aesthetic Fashion & Home Decor Boards
            "Clean Girl Capsule Wardrobe USA 2026",
            "Aesthetic Linen Outfits & Summer Styling",
            "Gold Layered Jewelry & Everyday Accessories",
            "Aesthetic Travertine & Marble Home Decor",
            "Cozy Bedroom & Warm Ambient Lighting",
            "Minimalist Coffee Table & Bookshelf Styling",
            # Viral & Amazon Bargain Boards (Highest Outbound CTR)
            "Amazon Beauty Finds Under $20",
            "Amazon Beauty Finds",
            "Affordable Skincare Finds 2026",
            "Viral TikTok Beauty Holy Grails 2026"
        ]
        real_price_display = product_price.strip() if product_price else "Check Today's Price"
        rev_k = f"{product_reviews // 1000}K+" if product_reviews >= 1000 else f"{product_reviews}"
        rating_display = f"{product_rating:.1f}★ ({rev_k} REVIEWS)" if product_rating > 0 else "4.8★ BESTSELLER"
        
        prompt = f"""
You are an Elite Pinterest Beauty Creative Director specializing in high-converting Pinterest affiliate pins for US women (ages 18–45).

STRICT PRICE & SOCIAL PROOF INTEGRITY RULES:
1. ACTUAL PRICE ENFORCEMENT: Use the EXACT Real Amazon Price ({real_price_display}) in the Title and Curiosity Hook!
   - If Actual Real Amazon Price is "{real_price_display}" (e.g. "$49" or "$49.99"), you MUST use "{real_price_display}" (or the exact dollar integer like "$49").
   - NEVER make up or hallucinate a different price (do NOT replace {real_price_display} with fake numbers like $14, $8, etc.)!
   - If Actual Real Amazon Price is empty or "Check Today's Price", do NOT write dollar amounts in title/hook!
2. Include Verified Social Proof Ratings ({rating_display}) in badge options to build 100% US buyer trust.

STRICT GEOGRAPHIC ROUTING RULE (USA 🇺🇸, UK 🇬🇧, CANADA 🇨🇦 ONLY):
1. Target 100% of content strictly for female shoppers in the United States 🇺🇸, United Kingdom 🇬🇧, and Canada 🇨🇦.
2. In Title, Description, Alt-Text, and Tags, explicitly embed Western geographic search terms (e.g., "Amazon US", "Sephora USA 2026", "UK Pharmacy Beauty", "Shoppers CA Favorites", "Clean Girl Aesthetic USA").
3. STRICT EXCLUSION: Explicitly exclude India, South Korea, Asia, and non-Western regions. Route 100% of Pinterest impressions, indexing, and feed distributions exclusively to USA, UK, and Canada users!

MISSION:
Create Pinterest pins and metadata that look like premium Sephora, Rhode, Rare Beauty, Summer Fridays, and luxury editorial campaigns while maximizing Outbound CTR and Saves.

DESIGN SYSTEM TEMPLATES (Rotate naturally):
- Template A: Minimal Luxury (Large centered product, editorial typography, white/cream background)
- Template B: Product + Beauty Texture (Cream, serum, lipstick smear, soft luxury lighting)
- Template C: Lifestyle Editorial (Product with model using it, magazine aesthetic)
- Template D: Vanity Setup (Product on marble tray, flowers, mirror reflection, luxury bathroom)
- Template E: Flat Lay (Product with accessories, clean minimal composition)

BACKGROUND & VISUAL AESTHETIC:
Ivory, Soft Beige, Warm White, Marble, Travertine, Vanity Table, Premium Bathroom, Luxury Fabric. Avoid busy/cluttered backgrounds.

Input variables:
Product Title: {product_title}
Actual Real Amazon Price: {real_price_display}
Verified Customer Rating: {rating_display}
Product Description: {product_desc}
Allowed Boards: {", ".join(allowed_boards)}.

HOOKS & CTA ROTATION:
- Hooks: "The $8 Amazon Lip Oil That Replaces $40 Dior", "The $12 Amazon Acne Patch That Erases Pimples Overnight", "This $19 Biodance Mask Gives Overnight Glass Skin", "Don't Buy Heavy Sunscreens Until You Try This $14 Zero White Cast SPF", "ONE/SIZE $18 Waterproof Spray Keeps Makeup Locked In 90° Heat", "Medicube $19 Zero Pore Pad Secret For Flawless Skin", "Back-To-School 5-Minute Skincare Routine That Erased My Acne In 7 Days", "The $8 e.l.f. Lip Oil That Replaces $40 Dior (Back-To-School Deal)"
- TIERED PRIORITY ROTATION PROTOCOL:
  * Tier 1 Mega-Virals (70% Allocation): Prioritize top high-CTR bestsellers: Biodance Collagen Mask ($19), Beauty of Joseon SPF 50 ($14), e.l.f. Glow Reviver Lip Oil ($8 Dior Dupe), ONE/SIZE Waterproof Spray ($18), Hero Cosmetics Mighty Patch ($12), TirTir Cushion Foundation ($15), Sol de Janeiro Cheirosa Mists ($24), Laneige Lip Mask ($19), Glow Recipe Dew Drops ($18), Medicube Zero Pore Pad ($19).
- Badges: Maximum ONE badge (e.g. "★ Under $15", "★ Under $20", "★ Bestseller", "★ 4.8 Rating" - only if verified)
- CTAs: "Shop Now →", "View on Amazon →", "See Today's Price →", "Check Price on Amazon →"

Input variables:
Product Title: {product_title}
Product Description: {product_desc}
Allowed Boards: {", ".join(allowed_boards)}

Return ONLY a single valid JSON object with keys "image_headline", "curiosity_hook", "title", "description", "alt_text", "tags", "board", "design_template", "cta_text", "badge_text", "quality_scores" and nothing else.

- Board: MUST be the exact 100% product-matched long-tail board from Allowed Boards list that perfectly matches the product category.
- Badge_text: MUST be a 100% product-matched 1-2 word luxury aesthetic category/intent tag (e.g., "DIOR DUPE", "KOREAN SKINCARE", "OVERNIGHT MASK", "ZERO WHITE-CAST", "GLASS SKIN"). NEVER include price numbers in badge_text!
- Curiosity_hook: strictly 6–12 words; high-converting PRICE MENTION curiosity overlay hook phrase (e.g., "The $8 Amazon Lip Oil That Replaces $40 Dior" or "This $12 Amazon Acne Patch Erased My Pimple in 7 Hours").
- Title: strictly 60–80 characters (Default target: 70 characters max); generate a high-converting PRICE MENTION SEO title formatted as: [Price/Dupe Hook (e.g. The $8 Amazon Lip Oil...)] + [Product Name] + [High-Volume Search Keyword US/UK/CA]; no emojis; title case. (Example: "The $8 Amazon Lip Oil That Replaces $40 Dior (Back-To-School Deal)")
- Description: strictly 400–450 characters; high-converting viral editorial copy targeted for USA 🇺🇸, UK 🇬🇧, and Canada 🇨🇦 female beauty shoppers. First 150 characters MUST be a high-volume search intent query (e.g., "Looking for the best Korean sunscreen for sensitive skin that leaves zero white cast for dewy glass skin?"). Include explicit CTA ("Shop on Amazon"). End with 5 viral targeted hashtags (e.g., "#AmazonBeautyFinds #KoreanSkincare #LipOilDupe #SephoraDupes #BeautyRoutine2026") followed by "💾 Save this pin!" as the last line.
- Alt_text: strictly 400–450 characters; Dominant Visual Search Indexing Format for Millions of Pinterest impressions: Stack 5 high-volume search intent queries into a seamless visual description: [Exact Product Name] + [3 Problem-Solving Search Intent Phrases (e.g., zero white cast sunscreen under makeup, acne-prone lightweight moisturizer, Korean glass skin routine)] + [Visual Scene & Texture (champagne travertine, cream smear, soft studio glow, minimalist ivory white product card with upper right price tag sticker)] + [Aesthetic Search Clusters (Clean Girl Aesthetic, Sephora Luxury Beauty, Amazon Beauty Finds 2026 USA UK Canada)]. Maximize Pinterest Lens and Search Feed #1 ranking dominance.
- Tags: comma-separated list of exactly 10 keywords (US/UK/Canada Amazon viral search terms).
- Board: choose best matching board from Allowed Boards using keyword relevance.
- Design_template: pick one of ["Template A", "Template B", "Template C", "Template D", "Template E"].
- Cta_text: select one CTA from approved rotation list (e.g. "View on Amazon →").
- Badge_text: 1-2 word category string (e.g., "KOREAN SKINCARE", "DIOR DUPE").
- Quality_scores: object with scores out of 100 for luxury_score, ctr_score, pinterest_score, mobile_score, trust_score, brand_consistency. ALL MUST BE >= 90.

Validation: if any rule fails or scores < 90, regenerate internally before returning valid JSON.

Output JSON Format Example:
{{
  "image_headline": "Hyaluronic Glow Serum",
  "curiosity_hook": "This $14 Serum Cleared My Acne & Dark Spots in 7 Days",
  "title": "The $14 Amazon Hyaluronic Glow Serum That Cleared Dark Spots — Glass Skin Routine",
  "description": "Looking for the best hydrating serum for dry skin to get glowing Korean glass skin in the US, UK, and Canada? This dermatologist recommended hyaluronic serum deeply plumps and locks moisture all day for a dewy luxury finish. Shop on Amazon for instant glow. #GlassSkin #AmazonBeautyFinds #KoreanSkincare #SephoraDupes #GlowSerum 💾 Save this pin!",
  "alt_text": "Close-up of a clear glass dropper bottle of Hyaluronic Glow Serum positioned on a minimalist warm ivory background inside a rounded white product card with a green price tag badge; glossy dewy gel texture on back of hand; model with poreless glass skin wearing Clean Girl Aesthetic makeup under warm studio lighting; referencing Sephora Beauty Dupes, TikTok Beauty Trends, and Amazon Skincare Favorites USA UK Canada 2026.",
  "tags": "hyaluronic acid serum,glass skin serum,dewy skin,hydrating serum,plumping serum,dermatologist recommended,clean beauty,tiktok beauty trends,sephora favorites,glow serum",
  "board": "Glow Serums & Glass Skin",
  "design_template": "Template B",
  "cta_text": "View on Amazon →",
  "badge_text": "GLASS SKIN",
  "quality_scores": {{
    "luxury_score": 98,
    "ctr_score": 97,
    "pinterest_score": 99,
    "mobile_score": 96,
    "trust_score": 98,
    "brand_consistency": 97
  }}
}}
"""
        response_text = await self._send_prompt(prompt, image_path=image_path)
        
        # Parse JSON
        try:
            # Extract content between first { and last }
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_json = response_text[start_idx:end_idx + 1].strip()
            else:
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                
            data = json.loads(clean_json)
            raw_headline = data.get("image_headline", "").strip()
            if not raw_headline or len(raw_headline.split()) > 7:
                # Fallback to first 5 words of product title
                raw_headline = " ".join(product_title.split()[:5])

            seo_data = PinterestSEOData(
                title=data.get("title", product_title[:100]).strip(),
                description=data.get("description", "Check out this amazing beauty product on Amazon!").strip(),
                alt_text=data.get("alt_text", f"A detailed product shot of {product_title}").strip()[:400],
                tags=data.get("tags", "beauty, skincare, shopping, makeup").strip(),
                board=data.get("board", "Amazon Beauty Finds").strip(),
                image_headline=raw_headline,
                curiosity_hook=data.get("curiosity_hook", "").strip()
            )
            return None, seo_data
        except Exception as e:
            logger.error(f"Failed to parse SEO JSON: {e}")
            fallback_headline = " ".join(product_title.split()[:5])

            fallback_desc = f"Looking for the best {product_title} for your beauty routine? Discover this top-rated Amazon find for glowing glass skin. Buy on Amazon. #BeautyFinds 💾 Save this pin!"
            fallback_alt = f"A high-quality aesthetic product shot showing the details of {product_title} placed on a clean marble surface with natural California sunlight, matching the Clean Girl Makeup and TikTok Beauty Trends aesthetic."[:400]
            
            return None, PinterestSEOData(
                title=product_title[:70], 
                description=fallback_desc, 
                alt_text=fallback_alt, 
                tags="beauty, skincare, makeup, shopping", 
                board="Amazon Beauty Finds",
                image_headline=fallback_headline
            )

    async def generate_product_idea(self, niche: str = "latest beauty products", past_products: list[str] = None, live_trends: str = "", google_trends: str = "", amazon_best_sellers: str = "") -> str:
        """
        Ask Gemini for a highly specific, trending product keyword using live Pinterest trends.
        """
        past_str = ""
        if past_products:
            past_str = "\nDO NOT suggest any of these products, as I have already posted them:\n" + "\n".join(f"- {p}" for p in past_products)

        trends_str = ""
        if live_trends:
            trends_str = f"\nLIVE PINTEREST TRENDS TODAY:\n{live_trends}\n(Use these to inspire your beauty product choice if relevant!)\n"

        prompt = f"""
###############################################################
PINTEREST SHOPPING TRENDS NAVIGATION
###############################################################

PRODUCT PRIORITIZATION RULES (CRITICAL FOR BADDIES BEAUTY v4.0):
- 100% STRICT RULE: BEAUTY PRODUCTS ONLY. Never generate fashion, apparel, clothing, jewelry, cups, books, or home decor.
- Allowed Categories (Select ONLY from these 10 categories):
  1. Skincare (Serums, Toners, Cleansers, Exfoliants, K-Beauty Glass Skin)
  2. Hair Care (Hair Oils, Scalp Treatments, Shampoos, Hair Masks)
  3. Makeup (Foundations, Blushes, Bronzers, Primers, Mascara, Dupes)
  4. Body Care (Body Scrubs, Body Oils, Lotions, Body Mists, Body Wash)
  5. Nail Care (Press-on Nails, Gel Nail Polish Kits, Cuticle Oils)
  6. Beauty Tools (Gua Sha, Facial Rollers, Blowout Brushes, Eyelash Curlers)
  7. Beauty Devices (LED Face Masks, Microcurrent Devices, IPL Hair Removal)
  8. Lip Care (Lip Oils, Lip Butter Balms, Lip Masks, Lip Tints)
  9. Sunscreen (Korean Sunscreens, SPF 50 Face Fluid, Tinted Sunscreen)
  10. Perfume (Viral Body Mists, Luxury Fragrances, Arabian Perfumes)
- IMPORTANT: Prioritize highly aesthetic, viral beauty items that feel like Sephora, Rhode, Dior Beauty, and Rare Beauty editorial campaigns.

This is the FIRST task.
Do not guess.
Do not search manually.
Follow these steps exactly.

---------------------------------------------------------------
STEP 1
---------------------------------------------------------------
Open: https://trends.pinterest.com
Wait until the website is fully loaded.

---------------------------------------------------------------
VIRAL US, UK & CANADA BEAUTY BRANDS & PRODUCTS REFERENCE (A to Z INSPIRATION):
---------------------------------------------------------------
You MUST select a completely unique brand and product category every single cycle. Do not repeat categories or brands in consecutive cycles.
Here is a list of popular US, UK & Canada categories and products to choose from for variety:
- 💎 High-Ticket Beauty Tech & Tools (PRIORITY FOR HIGH COMMISSION):
  * Dyson Airwrap Multi-Styler
  * Shark FlexStyle Air Styling System
  * Omnilux Contour Face LED Mask
  * Dr. Dennis Gross DRx SpectraLite FaceWare Pro
  * NuFACE Trinity Facial Toning Device
  * Braun Silk Expert Pro 5 IPL Hair Removal
  * Foreo UFO 2 Deep Facial Treatment
- 🌸 Skincare & K-Beauty (Glass Skin, UK & Canada Winter Classics):
  * First Aid Beauty Ultra Repair Cream (Canada #1 Cold Weather Barrier Moisturizer)
  * Caudalie Vinoperfect Radiance Dark Spot Serum (Sephora CA #1 Serum)
  * Weleda Skin Food (UK #1 Cult Favorite Base Glow)
  * The Ordinary Glycolic Acid 7% Toning Solution (UK & Canada #1 Exfoliating Toner)
  * La Roche-Posay Anthelios UVMune 400 SPF 50+ (UK #1 Sunscreen)
  * CeraVe SA Smoothing Cream (UK & CA Pharmacy Favorite)
  * Anua Heartleaf 77% Soothing Toner
  * COSRX Snail Mucin 96% Power Essence
  * Beauty of Joseon Relief Sun SPF 50
  * Round Lab Birch Juice Moisturizing Sunscreen
  * Skin1004 Madagascar Centella Ampoule
  * Tatcha The Water Cream
  * Paula's Choice 2% BHA Liquid Exfoliant
  * Glow Recipe Watermelon Glow Dew Drops
  * Biodance Bio-Collagen Real Deep Mask
  * Hero Cosmetics Mighty Patch Original
  * Medicube Zero Pore Pad 2.0
- ✨ Luxury Fragrances & UK/CA Tanners:
  * St. Tropez Express Bronzing Mousse (UK & CA #1 Self Tanner)
  * Baccarat Rouge 540 Eau de Parfum
  * Sol de Janeiro Brazilian Crush Cheirosa 68 & 62
  * Yves Saint Laurent Black Opium
  * Kayali Vanilla 28
  * Maison Margiela Replica Jazz Club & By the Fireplace
  * Carolina Herrera Good Girl
  * Parfums de Marly Delina
- Makeup & Lip Care (US, UK & Canada Favorites):
  * Nudestix Nudies Cream Blush Stick (Canada #1 Multi-Use Cream Blush)
  * Lanolips 101 Ointment Multipurpose Balm (Canada #1 Cold Weather Lip Repair)
  * e.l.f. Glow Reviver Lip Oil ($8 Dior Dupe)
  * e.l.f. Halo Glow Liquid Filter (UK & CA #1 Charlotte Tilbury Dupe)
  * NYX Professional Makeup Fat Oil Lip Drip
  * Rhode Pocket Blush & Peptide Lip Treatment
  * Rare Beauty Soft Pinch Liquid Blush
  * Charlotte Tilbury Hollywood Flawless Filter
  * Fenty Beauty Gloss Bomb Lip Luminizer
  * Summer Fridays Lip Butter Balm (Sephora CA #1 Lip Balm)
  * Merit Flush Balm Cream Blush
  * Huda Beauty Easy Bake Loose Powder
  * Milk Makeup Hydro Grip Primer
  * Tower 28 ShineOn Jelly Lip Gloss
  * Laneige Lip Sleeping Mask
- Body Care & Hair Care (US, UK & Canada Bestsellers):
  * Moroccanoil Treatment Original (Canada #1 Dryness & Frizz Hair Oil)
  * Color Wow Dream Coat Supernatural Spray (UK & CA #1 Anti-Frizz Spray)
  * Sol de Janeiro Brazilian Bum Bum Cream
  * Tree Hut Shea Sugar Body Scrub
  * Necessaire The Body Wash
  * Osea Undaria Algae Body Oil
  * EOS Shea Better Cashmere Vanilla Body Lotion
  * Olaplex No. 3 Hair Perfector
  * K18 Leave-In Molecular Repair Mask
  * Gisou Honey Infused Hair Oil
  * Mielle Organics Rosemary Mint Hair Oil
- Eye Care:
  * Peter Thomas Roth Instant FIRMx Eye
  * Shiseido Benefiance Wrinkle Smoothing Eye Cream
  * Laneige Water Bank Eye Cream
  * RoC Retinol Correxion Eye Cream
  * Cetaphil Hydrating Eye Gel-Cream

---------------------------------------------------------------
COMPREHENSIVE BEAUTY TOPICS & NICHES (FOR EXTRA INSPIRATION):
---------------------------------------------------------------
- 🌸 Skincare: Facial Cleansers, Face Wash, Cleansing Balms, Cleansing Oils, Toners, Essences, Face Mists, Serums, Ampoules, Moisturizers, Face Creams, Night Creams, Day Creams, Gel Moisturizers, Sleeping Masks, Sheet Masks, Clay Masks, Peel-Off Masks, Exfoliators, Chemical Exfoliants, Face Scrubs, Eye Creams, Eye Patches, Lip Masks, Lip Balms, Sunscreens, SPF Sticks, Acne Treatments, Dark Spot Treatments, Anti-Aging Skincare, Retinol Products, Vitamin C Skincare, Niacinamide Products, Hyaluronic Acid Products, Peptide Skincare, Ceramide Skincare, Barrier Repair Products, Glass Skin Products, Sensitive Skin Products, Oily Skin Products, Dry Skin Products, Combination Skin Products
- 💄 Makeup: Foundation, Concealer, BB Cream, CC Cream, Primer, Setting Spray, Setting Powder, Compact Powder, Blush, Bronzer, Highlighter, Contour, Eyeshadow, Eyeliner, Mascara, False Eyelashes, Brow Gel, Brow Pencil, Lipstick, Lip Gloss, Lip Oil, Lip Tint, Lip Liner, Makeup Brushes, Makeup Sponge, Makeup Remover
- 💇 Hair Care: Shampoo, Conditioner, Hair Masks, Hair Oils, Hair Serums, Hair Growth Products, Hair Repair Treatments, Bond Repair Products, Leave-In Conditioner, Heat Protectant, Dry Shampoo, Curl Cream, Hair Styling Products, Hair Spray, Hair Wax, Hair Mousse, Hair Color, Hair Toners, Purple Shampoo, Scalp Care, Scalp Serums, Hair Vitamins
- 🛁 Body Care: Body Wash, Shower Gel, Body Scrubs, Sugar Scrubs, Salt Scrubs, Body Lotion, Body Butter, Body Oil, Body Serum, Cellulite Cream, Firming Cream, Stretch Mark Cream, Hand Cream, Foot Cream, Deodorant, Whole Body Deodorant, Bath Bombs, Bath Salts, Feminine Care
- 🌞 Sun Care: Face Sunscreen, Body Sunscreen, Mineral Sunscreen, Chemical Sunscreen, SPF Lip Balm, After Sun Care, Self Tanner, Bronzing Lotion, Tanning Oil
- 💅 Nails: Nail Polish, Gel Nail Polish, Nail Strengthener, Cuticle Oil, Nail Art, Press-On Nails, Nail Tools
- 🦷 Oral Beauty: Teeth Whitening, Whitening Strips, Whitening Pens, Electric Toothbrush, Water Flosser, Mouthwash, Whitening Toothpaste
- 🌸 Fragrance: Perfume, Body Mist, Hair Perfume, Perfume Oils, Travel Perfume, Luxury Fragrance
- 🧰 Beauty Tools: LED Face Masks, Facial Cleansing Brushes, Ice Rollers, Gua Sha, Jade Roller, Derma Roller, Facial Steamers, Blackhead Removers, Makeup Mirrors, Makeup Organizers, Hair Dryers, Hair Straighteners, Curling Irons, Air Stylers, Hot Air Brushes, Epilators, Facial Hair Removers
- 🇰🇷 K-Beauty: Korean Skincare, Korean Sunscreens, Korean Cleansers, Korean Toners, Korean Serums, Korean Moisturizers, Korean Sheet Masks, Korean Lip Care, Korean Makeup
- 🌿 Clean Beauty: Organic Beauty, Vegan Beauty, Cruelty-Free Beauty, Clean Skincare, Natural Beauty Products, Fragrance-Free Skincare
- ✨ Trending Beauty: TikTok Beauty Trends, Viral Amazon Beauty Finds, Sephora Favorites, Ulta Best Sellers, Luxury Beauty, Drugstore Beauty, Anti-Aging, Glass Skin, Clean Girl Beauty, Summer Beauty, Winter Skincare, Wedding Makeup, Holiday Beauty, Travel Beauty, Beauty Gift Sets, Self-Care Essentials, Spa at Home, Beauty Hacks
- 📅 Seasonal & Event-Based: Spring Beauty, Summer Beauty, Fall Skincare, Winter Hydration, Valentine's Beauty, Mother's Day Gifts, Easter Beauty, Memorial Day Deals, Fourth of July Beauty, Back to School Beauty, Halloween Makeup, Black Friday Beauty, Cyber Monday Deals, Christmas Beauty Gifts, New Year Glow
- 💡 Problem & Solution: Acne Solutions, Acne Scar Treatment, Dark Spots, Hyperpigmentation, Rosacea Care, Sensitive Skin, Oily Skin, Dry Skin, Large Pores, Fine Lines, Wrinkles, Puffy Eyes, Dark Circles, Hair Loss, Frizzy Hair, Damaged Hair, Split Ends, Thin Hair, Dandruff, Body Acne, Keratosis Pilaris, Chapped Lips
- 💸 Budget Finds & Steals: Under $10 Beauty, Under $15 Beauty, Under $20 Beauty, Under $25 Beauty, Under $50 Beauty, Luxury Dupes, Drugstore Beauty, Affordable Makeup, Affordable Skincare, Amazon Deals, Prime Day Beauty, Beauty Steals
- 📱 Viral Social Trends: TikTok Made Me Buy It, Viral Amazon Finds, Sephora Viral, Ulta Favorites, Clean Girl Aesthetic, Glass Skin, Korean Beauty, Quiet Luxury Beauty, Vanilla Girl Beauty, Latte Makeup, Strawberry Makeup, Glazed Donut Skin
- 🧘‍♀️ Lifestyle Beauty: Self Care Sunday, Morning Routine, Night Routine, Gym Beauty, Travel Beauty, Bridal Beauty, Vacation Essentials, College Beauty, Mom Beauty, Office Makeup

---------------------------------------------------------------
STEP 2
---------------------------------------------------------------
Look at the LEFT SIDEBAR.
You will see three options.
1. Trend Overview
2. Shopping Trends
3. Search Trends

Click ONLY: Shopping Trends
Wait until the Shopping Trends page is fully loaded.

---------------------------------------------------------------
STEP 3
---------------------------------------------------------------
Verify the Region.
If Region is not: United States
Change it to: United States
Wait until the page refreshes completely.

---------------------------------------------------------------
STEP 4
---------------------------------------------------------------
At the top of the page you will see two tabs.
• Trending Categories
• All Categories

Click: All Categories
Wait until all categories load.

---------------------------------------------------------------
STEP 5
---------------------------------------------------------------
After clicking All Categories,
Look for the category tile named: Beauty

Click: Beauty
Wait until all Beauty product categories appear.

---------------------------------------------------------------
STEP 6
---------------------------------------------------------------
You are now inside the Beauty section.
Here is the complete list of Pinterest Beauty subcategories you must choose from:
- Bath & body
- Bath & shower
- Beauty supplements
- Blushes & bronzers
- Body care
- Body makeup
- Body moisturizers
- Body washes
- Brow makeup
- Deodorants & antiperspirants
- Eye makeup
- Eye shadow
- Eyeliners
- Face lotions & creams
- Face makeup
- Facial cleansers
- Facial moisturizers
- False eyelashes
- Foundations & concealers
- Fragrance
- Hair
- Hair accessories
- Hair care
- Hair color
- Hair combs
- Hair pins, claws & clips
- Hair removal
- Hair tools
- Hair treatment
- Hair wreaths
- Hand & foot care
- Hand soaps & sanitizers
- Razors & shaving tools
- Serums & essences
- Shampoo & conditioner
- Skincare
- Skincare masks & peels
- Sunscreen
- Tanning oils & lotions
- Teeth whitening
- Teeth whitening tools
- Tiaras
- Toners & astringents
- Veils
- Wigs & hair extensions

---------------------------------------------------------------
STEP 7
---------------------------------------------------------------
For this specific research cycle, your target subcategory is: {niche}
Imagine clicking and opening the subcategory "{niche}" from the list above.
Wait until the category page loads.

---------------------------------------------------------------
STEP 8
---------------------------------------------------------------
Scroll down.
Find the section: Top Products On Pinterest

If needed, click: Explore Top Products
Wait for the popup or product list.

---------------------------------------------------------------
STEP 9
---------------------------------------------------------------
Read every product name.
Merchant does NOT matter.
Amazon, Target, Sephora, Ulta, Walmart, CVS, Native, SHEIN
Any merchant is acceptable.

Your goal is ONLY to find ONE trending beauty product.

---------------------------------------------------------------
STEP 10
---------------------------------------------------------------
Copy ONLY the Product Name.
Do not choose more than one product.
After selecting one product, stop Pinterest research and continue to the Amazon workflow.

---------------------------------------------------------------
IMPORTANT
---------------------------------------------------------------
Never skip steps.
Always wait 2–3 seconds after every click.
Always wait until the page is completely loaded.
Never rush.
Never use Search.
Always navigate using:
Shopping Trends
↓
All Categories
↓
Beauty
↓
Beauty Category
↓
Top Products
↓
Choose One Product
↓
Continue to Amazon.

PRODUCT ROTATION & GLOBAL TARGETING MANDATE:
- Rotate across categories: Skincare, Hair Care, Makeup, Lip Care, Fragrance, Body Care, Tools, Back-to-School, UK Bestsellers, Canada Bestsellers.
- NEVER pick a product that is present in the past published list.
- Maintain a balanced distribution: US Viral (60%), UK Boots/Cult Beauty Viral (20%), Canada Shoppers/Sephora CA Viral (20%).
- Ensure high-converting variety in every research cycle.

{trends_str}

{past_str}

Return only ONE final product per research cycle. Wrap your choice inside <product> and </product> tags with NO extra explanations or step numbers outside the tags.
Example: <product>COSRX Snail Mucin 96% Power Repairing Essence</product>
"""
        response = await self._send_prompt(prompt)
        
        import random
        fallback_beauty = [
            "Biodance Bio-Collagen Real Deep Mask",
            "Beauty of Joseon Relief Sun SPF 50 Rice Probiotics",
            "Medicube Zero Pore Pad 2.0 Exfoliating Toner Pad",
            "COSRX Advanced Snail 96 Mucin Power Essence",
            "Anua Heartleaf 77 Soothing Toner",
            "Skin1004 Madagascar Centella Hyalu-Cica Water-Fit Sun Serum",
            "Torriden DIVE-IN Low Molecular Hyaluronic Acid Serum",
            "d'Alba Piedmont White Truffle First Spray Serum",
            "Kahi Wrinkle Bounce Multi Balm",
            "TirTir Mask Fit Red Cushion Foundation",
            "Illiyoon Ceramide Ato Concentrate Cream",
            "Mixsoon Bean Essence Hydrating Exfoliator",
            "Round Lab Birch Juice Moisturizing Sunscreen SPF 50+",
            "Numbuzin No.3 Super Glowing Essence Toner",
            "Haruharu Wonder Black Rice Hyaluronic Toner",
            "I'm From Rice Toner Brightening Hydrating",
            "Aestura Atobarrier 365 Cream Barrier Repair",
            "Tocobo Bio Watery Sun Cream SPF50+",
            "VT Cosmetics Reedle Shot 100 Boosting Shot",
            "e.l.f. Glow Reviver Lip Oil",
            "ONE/SIZE Patrick Starrr On 'Til Dawn Waterproof Setting Spray",
            "Hero Cosmetics Mighty Patch Original Hydrocolloid Acne Patch",
            "Summer Fridays Lip Butter Balm Vanilla",
            "Summer Fridays Lip Butter Balm Cherry",
            "Laneige Lip Sleeping Mask Berry",
            "Glow Recipe Watermelon Glow Niacinamide Dew Drops",
            "Rare Beauty Soft Pinch Liquid Blush",
            "Dior Addict Lip Glow Oil 001 Pink",
            "Sol de Janeiro Cheirosa 68 Beija Flor Perfume Mist",
            "Sol de Janeiro Cheirosa 59 Delicia Drench Perfume Mist",
            "Sol de Janeiro Cheirosa 62 Brazilian Crush Mist",
            "Paula's Choice 2% BHA Liquid Salicylic Acid Exfoliant",
            "Caudalie Vinoperfect Radiance Dark Spot Serum",
            "Dyson Airwrap Multi-Styler Nickel Copper",
            "Charlotte Tilbury Hollywood Flawless Filter",
            "Charlotte Tilbury Magic Cream Hydrating Moisturizer",
            "Refy Beauty Lip Gloss Clear",
            "Refy Brow Sculpt Shape and Hold Gel",
            "Saie Glowy Super Gel Lightweight Dewy Highlighter",
            "Tower 28 Beauty SOS Daily Facial Rescue Spray",
            "Supergoop! Unseen Sunscreen SPF 40",
            "Fenty Beauty Gloss Bomb Universal Lip Luminizer",
            "K18 Leave-In Molecular Repair Hair Mask",
            "Olaplex No. 3 Hair Perfector Repairing Treatment",
            "Color Wow Dream Coat Supernatural Anti-Frizz Spray",
            "Color Wow Extra Strength Dream Coat",
            "Moroccanoil Treatment Original Hair Oil",
            "Gisou Honey Infused Hair Oil",
            "Ouai Detox Shampoo Clarifying Scalp Treatment",
            "Amika Soulfood Nourishing Hair Mask",
            "Shark FlexStyle Air Styling & Drying System",
            "Tatcha The Dewy Skin Cream Plumping Hydrator",
            "Drunk Elephant D-Bronzi Anti-Pollution Sunshine Drops",
            "Weleda Skin Food Original Ultra-Rich Cream",
            "The Ordinary Glycolic Acid 7% Toning Solution",
            "La Roche-Posay Anthelios UVMune 400 Invisible Fluid SPF50+",
            "La Roche-Posay Cicaplast Baume B5+ Soothing Repairing Balm",
            "Avene Cicalfate+ Restorative Protective Cream",
            "Bioderma Sensibio H2O Micellar Water Cleanser",
            "CeraVe Hydrating Cleanser Non-Foaming",
            "CeraVe Resurfacing Retinol Serum for Post-Acne Marks",
            "L'Oreal Paris Revitalift Filler 1.5% Pure Hyaluronic Acid Serum",
            "No7 Future Renew Damage Reversal Serum",
            "Pixi Glow Tonic 5% Glycolic Acid Exfoliating Toner",
            "Byoma Hydrating Serum Ceramide Tri-Complex",
            "Byoma Creamy Jelly Cleanser",
            "Simple Kind to Skin Hydrating Light Moisturiser",
            "Embryolisse Lait-Creme Concentre Miracle Cream",
            "First Aid Beauty Ultra Repair Cream Intense Hydration",
            "The Ordinary Niacinamide 10% + Zinc 1%",
            "The Ordinary AHA 30% + BHA 2% Peeling Solution",
            "Nudestix Nudies Matte All Over Face Blush Color",
            "Marc Anthony Strictly Curls Curl Defining Lotion",
            "Burt's Bees 100% Natural Tinted Lip Balm",
            "Vaseline Lip Therapy Rosy Lips Tin",
            "Aquaphor Healing Ointment Dry Skin Protectant",
            "Tree Hut Shea Sugar Body Scrub Tropical Mango",
            "Tree Hut Shea Sugar Body Scrub Moroccan Rose",
            "EOS Shea Better Body Lotion Vanilla Cashmere",
            "Nécessaire The Body Wash Eucalyptus",
            "L'Occitane Almond Shower Oil Hydrating Cleanser",
            "Sol de Janeiro Bum Bum Cream Tightening Cream",
            "PanOxyl Acne Foaming Wash 10% Benzoyl Peroxide",
            "Cerave SA Cleanser Salicylic Acid Smooth Skin",
            "e.l.f. Halo Glow Liquid Filter",
            "e.l.f. Power Grip Primer + 4% Niacinamide",
            "Milani Make It Last 16HR Setting Spray",
            "Maybelline Lash Sensational Sky High Waterproof Mascara",
            "NYX Fat Oil Lip Drip Lip Gloss",
            "L'Oreal Paris Telescopic Lift Mascara",
            "Essence Lash Princess False Lash Effect Mascara",
            "Real Techniques Everyday Eye Essentials Makeup Brush Set",
            "Touchland Power Mist Hydrating Hand Sanitizer Berry Bliss",
            "Maison Francis Kurkdjian Baccarat Rouge 540 Dupe Lattafa Ana Abiyedh",
            "Phlur Missing Person Eau de Parfum",
            "Glossier You Eau de Parfum Solid",
            "Sabrina Carpenter Sweet Tooth Eau de Parfum",
            "Billie Eilish Eau de Parfum Vanilla Amber"
        ]

        if response:
            import re
            match = re.search(r'<product>(.*?)</product>', response, re.DOTALL | re.IGNORECASE)
            if match:
                res_clean = match.group(1).strip().replace('"', "")
                if len(res_clean) >= 5 and not any(w in res_clean.lower() for w in ["trending", "beauty trend", "trend product", "selected product"]):
                    return res_clean
            lines = [l.strip().replace('"', '').replace('*', '').replace('`', '') for l in response.strip().split('\n') if l.strip()]
            for l in lines:
                l_clean = l
                for prefix in ["Category:", "Product:", "Keyword:", "Selected product keyword:", "Recommended:", "Selected:", "Selected Beauty Trend Product:"]:
                    if l_clean.lower().startswith(prefix.lower()):
                        l_clean = l_clean[len(prefix):].strip()
                l_lower = l_clean.lower()
                if l_clean.startswith("#") or l_clean.startswith("🌟") or "why this" in l_lower or "trending beauty" in l_lower or "beauty trend" in l_lower or "trend product" in l_lower or "recommended" in l_lower or l_lower.startswith("category"):
                    continue
                if len(l_clean) >= 5 and len(l_clean) <= 70:
                    return l_clean

        past_set = set(p.lower().strip() for p in (past_products or []))
        valid_fallbacks = [f for f in fallback_beauty if f.lower().strip() not in past_set]
        if valid_fallbacks:
            return random.choice(valid_fallbacks)
        return random.choice(fallback_beauty)

    async def detect_viral_trend_bypass(self, trends_list: str, allowed_categories: list[str]) -> dict[str, Any] | None:
        """
        Ask Gemini if there is a strong viral beauty product trending in the trends list.
        """
        prompt = f"""
Analyze these trending search terms from Google Trends and Pinterest Trends:
Trends List: {trends_list}

Allowed Categories: {", ".join(allowed_categories)}

Is there any specific, concrete beauty product, skincare item, makeup product, hair styling tool, nail art trend, or fragrance that is currently trending and has high search volume?
The product keyword must be suitable for searching on Amazon (e.g. "Snail Mucin", "Gua Sha", "Lash Growth Serum", "Waterproof Mascara", "Hair claws"). Avoid broad terms like "Beauty" or general news topics.

Return ONLY a single valid JSON object with the following keys and nothing else:
If a strong trend is found:
{{
  "trend_detected": true,
  "product_keyword": "<specific product keyword, max 4 words>",
  "category": "<one category selected from Allowed Categories>"
}}

If no specific beauty/wellness product is trending:
{{
  "trend_detected": false
}}
"""
        response_text = await self._send_prompt(prompt)
        try:
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if data.get("trend_detected") and data.get("product_keyword") and data.get("category"):
                    if data["category"] in allowed_categories:
                        return data
            return {"trend_detected": False}
        except Exception as e:
            logger.error("Failed to parse viral trend response: %s", e)
            return {"trend_detected": False}

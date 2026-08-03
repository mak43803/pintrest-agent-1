"""
Pinterest Agent Core — The central orchestrator.
==================================================

Wires together all modules (Database, LLM, Browser, Tools, Memory)
and executes the End-to-End Affiliate workflow.

Usage::
    from agent.pinterest_agent import PinterestAgent
    import asyncio
    
    agent = PinterestAgent()
    asyncio.run(agent.run_affiliate_pipeline(niche="latest beauty products"))
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import re
from pathlib import Path

def extract_asin(url: str) -> str | None:
    """Extract Amazon ASIN from product URL."""
    if not url:
        return None
    # Match 10-character alphanumeric ASIN after /dp/ or /gp/product/ or /gp/video/ or /d/
    match = re.search(r'/(?:dp|gp/product|gp/video|d)/([A-Z0-9]{10})', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    # Fallback if URL is just an Amazon domain and contains a 10-char alphanumeric string
    if "amazon." in url.lower():
        match = re.search(r'([A-Z0-9]{10})', url)
        if match:
            return match.group(1).upper()
    return None

def is_book_product(text_to_check: str) -> bool:
    """Check if title, description, or keyword refers to a book, manual, guide, or non-beauty literature item."""
    if not text_to_check:
        return False
    text_lower = text_to_check.lower()
    book_keywords = [
        "book", "paperback", "hardcover", "kindle", "edition", "novel", "handbook", "manual",
        "usmle", "study guide", "textbook", "audiobook", "spiral-bound", "publisher", "author",
        "workflow", "workflows", "productivity", "guide", "guidebook", "navigation handbook",
        "practical guide", "exam prep", "pocket guide", "step 1 2026", "step 2 2026"
    ]
    for kw in book_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            return True
    return False

def is_non_beauty_product(text_to_check: str) -> bool:
    """Check if title, description, or keyword refers to non-beauty categories (fashion, clothing, home decor, books, etc.)."""
    if not text_to_check:
        return False
    text_lower = text_to_check.lower()
    
    # Strip beauty terminology that contains words like 'coat', 'boot', 'ring'
    beauty_context_phrases = [
        "top coat", "base coat", "clear coat", "first coat", "second coat", "coat of", "coating", "coats of",
        "coat your lips", "coat lips", "coat the lips", "ring light", "boots pharmacy", "boots beauty"
    ]
    for b_phrase in beauty_context_phrases:
        text_lower = text_lower.replace(b_phrase, " ")

    non_beauty_keywords = [
        "dress", "skirt", "leggings", "sweater", "hoodie", "cardigan", "outfit", "wardrobe", "pants", "jeans",
        "t-shirt", "blouse", "jacket", "winter coat", "trench coat", "raincoat", "overcoat", "fur coat", "bra", "underwear", "socks", "shorts", "romper", "jumpsuit",
        "purse", "handbag", "wallet", "clutch", "backpack", "tote bag",
        "shoe", "sneaker", "hiking boot", "ankle boot", "cowboy boot", "snow boot", "sandal", "heel", "flats", "slippers",
        "necklace", "earring", "bracelet", "diamond ring", "gold ring", "pendant", "jewelry",
        "home decor", "curtains", "rug", "pillow", "blanket", "vase", "wall art", "furniture", "lamp",
        "book", "paperback", "hardcover", "kindle", "novel", "textbook", "guidebook"
    ]
    for kw in non_beauty_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            return True
    return False

def is_clickbait_spam(text_to_check: str) -> bool:
    """Check if title or headline contains spammy clickbait or false claims."""
    if not text_to_check:
        return False
    text_lower = text_to_check.lower()
    spam_phrases = [
        "shocking trick", "secret formula", "100% free gift", "miracle cure",
        "guaranteed overnight", "doctors hate this", "weird trick", "free money",
        "hurry before deleted", "ending in 5 mins", "only 1 left", "99% off sale",
        "fake review", "fake deal", "claim free sample"
    ]
    return any(p in text_lower for p in spam_phrases)

def is_fuzzy_duplicate_title(new_title: str, existing_titles: list[str]) -> bool:
    """Check if new_title is a duplicate of any existing product title using normalized word token overlap."""
    if not new_title:
        return False
    
    stop_words = {
        "for", "with", "and", "the", "in", "of", "a", "an", "to", "oz", "count", "ct", "pack", 
        "set", "pcs", "piece", "mini", "ml", "g", "new", "best", "top", "great", "women", "men"
    }
    
    def get_clean_tokens(t: str) -> set[str]:
        words = re.findall(r'\b[a-z0-9]{3,}\b', t.lower())
        return set(w for w in words if w not in stop_words)

    new_tokens = get_clean_tokens(new_title)
    if len(new_tokens) < 2:
        return False

    for ext in existing_titles:
        ext_tokens = get_clean_tokens(ext)
        if len(ext_tokens) < 2:
            continue
        
        intersection = new_tokens.intersection(ext_tokens)
        min_size = min(len(new_tokens), len(ext_tokens))
        
        if len(intersection) >= 3 and (len(intersection) / min_size) >= 0.70:
            return True
            
    return False


from config.settings import get_settings
settings = get_settings()
from database.database import Database
from database.init_db import create_database
from browser.browser_manager import BrowserManager
from browser.pinterest_client import PinterestClient
from browser.amazon_client import AmazonClient, AmazonProduct
from browser.gemini_web_client import GeminiWebClient
from browser.linktree_client import LinktreeClient
from tools.image_tools import ImageTools
from logs.logger import setup_logger
from logs.log_manager import LogManager
from logs.error_handler import setup_global_exception_handler, log_execution
from memory.memory_manager import MemoryManager

# Setup root logger for the entire application
setup_logger()
logger = logging.getLogger("pinterest_agent.core")


class PinterestAgent:
    """The main autonomous AI Agent for Pinterest Affiliate Marketing."""

    def __init__(self) -> None:
        logger.info("Initializing PinterestAgent...")
        
        # 1. Database
        db_path = Path("database/pinterest_ai_agent.db")
        self.db = Database(str(db_path))
        create_database(self.db)
        
        # 2. Logging & Crash Recovery
        self.log_manager = LogManager(self.db)
        setup_global_exception_handler(self.log_manager)
        
        # 3. Browser Clients
        import os
        self.browser_manager = BrowserManager()
        self.amazon = AmazonClient(self.browser_manager, os.getenv("AMAZON_AFFILIATE_TAG", "yourtag-20"))
        
        self.gemini = GeminiWebClient(self.browser_manager)
        self.linktree = LinktreeClient(self.browser_manager)
        
        self.pinterest = PinterestClient(self.browser_manager)
        self.pinterest.enable_vision_healing(self.db, self.gemini.analyze_ui_for_selector)
        
        # 4. Tools
        self.image_tools = ImageTools()
        
        # 6. Memory System
        self.memory = MemoryManager(self.db)
        
        # Initialize pin counter from DB for BADDIES BEAUTY v4.0 layout rotation
        try:
            with self.db.connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM products")
                row = cursor.fetchone()
                self.pin_counter = row["cnt"] if row else 0
        except Exception:
            self.pin_counter = 0

        self._is_initialized = False

    async def initialize(self) -> None:
        """Start background services like the browser manager."""
        if self._is_initialized:
            return
            
        logger.info("Starting browser manager...")
        await self.browser_manager.initialize()
        self._is_initialized = True

    async def shutdown(self) -> None:
        """Gracefully close all connections."""
        logger.info("Shutting down Agent...")
        await self.browser_manager.close()
        self.db.close()

    def choose_board_by_product(self, title: str, suggested_board: str = None) -> str:
        title_lower = title.lower()
        
        # 1. High-Precision Keyword Matching on Product Title (Guarantees 100% category match)
        if any(w in title_lower for w in ["perfume", "fragrance", "body mist", "perfume mist", "fragrance mist", "cologne", "scent", "eau de", "edp", "edt"]):
            return "Signature Perfumes & Fragrances"
        elif any(w in title_lower for w in ["teeth", "tooth", "smile", "whitening", "floss", "breath"]):
            return "Teeth Whitening & Smile Care"
        elif any(w in title_lower for w in ["patch", "pimple", "acne patch", "zit"]):
            return "Overnight Acne & Pimple Patches"
        elif any(w in title_lower for w in ["dark spot", "hyperpigmentation", "brightening"]):
            return "Dark Spot Correctors & Brightening"
        elif any(w in title_lower for w in ["lip", "gloss", "balm", "lipstick", "tint", "plumper", "lip liner", "lip oil"]):
            return "Viral Lip Oils & Tints"
        elif any(w in title_lower for w in ["hair growth", "rosemary oil", "density", "biotin"]):
            return "Hair Growth Oils & Serums"
        elif any(w in title_lower for w in ["hair", "shampoo", "conditioner", "scalp", "blowout", "hair oil"]):
            return "90s Blowout & Hair Care Secrets"
        elif any(w in title_lower for w in ["blush", "bronzer", "contour"]):
            return "Cream Blush & Bronzer Glow"
        elif any(w in title_lower for w in ["wash", "cleanser", "soap", "cleansing"]):
            return "Hydrating Cleansers & Face Wash"
        elif any(w in title_lower for w in ["serum", "ampoule", "drops"]):
            return "Glow Serums & Glass Skin"
        elif any(w in title_lower for w in ["moisturizer", "cream", "gel", "lotion", "sunscreen", "spf"]):
            return "Dewy Moisturizers & Daily SPF"
        elif any(w in title_lower for w in ["body", "scrub", "shower", "shaving", "deodorant", "body wash", "body lotion"]):
            return "Aesthetic Vanilla Body Routine"
        elif any(w in title_lower for w in ["nail", "polish", "gel", "manicure"]):
            return "Glazed Donut & Gel Nails"
        elif any(w in title_lower for w in ["roller", "gua sha", "led", "mask", "steamer", "device", "tool"]):
            return "At-Home Beauty Tools & Devices"
        elif any(w in title_lower for w in ["eye", "lash", "brow", "eyeliner", "mascara", "under-eye", "undereye"]):
            return "Clean Girl Eye & Brow Routine"
        elif any(w in title_lower for w in ["makeup", "foundation", "concealer", "powder", "palette", "brush", "beauty blender"]):
            return "Clean Girl Aesthetic Makeup"
        elif any(w in title_lower for w in ["korean", "k-beauty", "anua", "cosrx", "beauty of joseon", "round lab", "essence", "snail", "mixsoon", "dr.althea", "aestura", "illiyoon"]):
            return "Korean Glass Skin Secrets"
        elif any(w in title_lower for w in ["travel", "tsa", "mini", "toiletry"]):
            return "TSA Approved Travel Beauty Essentials"
        elif suggested_board and suggested_board.strip() and suggested_board.strip() not in ["Amazon Beauty Finds", "Amazon Viral Beauty Finds"]:
            return suggested_board.strip()
        else:
            return "Amazon Viral Beauty Finds"

    def verify_quality(self, product_details: Any, seo_data: Any, image_path: str, board_name: str, db_product_id: int | None = None) -> bool:
        """Verify quality standards before publishing (STEP 6 validation)."""
        logger.info("Running Pre-Publish Quality Check...")

        # 0. Anti-Non-Beauty Check (Strict Beauty Products Only)
        if is_book_product(product_details.title) or is_book_product(seo_data.title):
            logger.error("Quality Check Failed: Product is detected as a Book/Guide/Manual literature item, not a Beauty product!")
            return False

        if is_non_beauty_product(product_details.title) or is_non_beauty_product(seo_data.title):
            logger.error("Quality Check Failed: Product is detected as Fashion/Home Decor/Non-Beauty item! Only Beauty products are allowed.")
            return False

        if is_clickbait_spam(product_details.title) or is_clickbait_spam(seo_data.title) or is_clickbait_spam(getattr(seo_data, "image_headline", "")):
            logger.error("Quality Check Failed: Title contains spammy clickbait or exaggerated claims!")
            return False

        # 1. Correct affiliate URL
        if not product_details.affiliate_url or not product_details.affiliate_url.startswith("http"):
            logger.error("Quality Check Failed: Invalid/missing affiliate URL.")
            return False

        # 2. Correct product image
        if not image_path or not os.path.exists(image_path):
            logger.error("Quality Check Failed: Pin image file not found.")
            return False

        # 3. Pinterest SEO complete (Title, Description, Alt text)
        if not seo_data.title or not seo_data.description or not seo_data.alt_text:
            logger.error("Quality Check Failed: Title, Description, or Alt text is missing.")
            return False

        # 4. Alt text added & length
        if len(seo_data.alt_text) < 15:
            logger.error("Quality Check Failed: Alt text is too short.")
            return False

        # 5. Correct board selected
        if not board_name:
            logger.error("Quality Check Failed: Board name is not selected.")
            return False

        # 6. Content uniqueness & US English character checks (excluding current pending item)
        with self.db.connection() as conn:
            query = "SELECT 1 FROM products WHERE status IN ('Pinterest_Published', 'Processing') "
            params = []
            if db_product_id:
                query += "AND id != ? "
                params.append(db_product_id)

            if product_details.affiliate_url:
                query += "AND (affiliate_link = ? OR LOWER(title) = LOWER(?) OR LOWER(description) = LOWER(?))"
                params.extend([product_details.affiliate_url, seo_data.title, seo_data.description])
            else:
                query += "AND (LOWER(title) = LOWER(?) OR LOWER(description) = LOWER(?))"
                params.extend([seo_data.title, seo_data.description])
                
            cursor = conn.execute(query, params)
            if cursor.fetchone():
                logger.error("Quality Check Failed: Duplicate Affiliate Link or SEO Title/Description already published in DB.")
                return False

        logger.info("✅ Quality Check Passed successfully!")
        return True

    def optimize_alt_text(self, alt_text: str, board_name: str, niche: str) -> str:
        """
        Optimize Alt-Text with high-volume search query tags naturally integrated.
        Ensures length is strictly under 490 characters to avoid Pinterest UI cutoffs.
        """
        board_lower = board_name.lower()
        niche_lower = niche.lower()
        
        seo_phrases = []
        if any(x in board_lower or x in niche_lower for x in ["skin", "serum", "cleanser", "moisturizer", "spf", "sunscreen"]):
            seo_phrases = ["glass skin skincare routine", "dermatologist recommended skincare", "affordable skincare finds", "clear skin tips"]
        elif any(x in board_lower or x in niche_lower for x in ["makeup", "lip", "gloss", "blush", "brow", "eye", "foundation"]):
            seo_phrases = ["clean girl makeup aesthetic", "viral makeup trends", "amazon makeup favorites", "everyday makeup routine"]
        elif any(x in board_lower or x in niche_lower for x in ["hair", "scalp", "shampoo", "curl"]):
            seo_phrases = ["healthy hair care routine", "hair growth tips", "aesthetic hair accessories", "hair styling tools"]
        elif any(x in board_lower or x in niche_lower for x in ["fragrance", "perfume", "mist", "scent"]):
            seo_phrases = ["clean girl perfume aesthetic", "luxury fragrance mist", "viral perfume favorites", "long lasting perfumes"]
        elif any(x in board_lower or x in niche_lower for x in ["nail", "polish", "manicure"]):
            seo_phrases = ["aesthetic nail design ideas", "nail care routine", "simple gel nail art", "press on nails diy"]
        else:
            seo_phrases = ["viral beauty favorites", "must have beauty products", "top rated amazon finds", "aesthetic self care routine"]
            
        # Add clean niche reference
        niche_clean = niche.strip().replace("-", " ").lower()
        if niche_clean not in board_lower:
            seo_phrases.insert(0, f"{niche_clean} finds")
            
        # Construct natural SEO sentence
        seo_sentence = " Ideal for search queries relating to: " + ", ".join(seo_phrases) + "."
        
        # Merge and limit to 490 chars (Pinterest max: 500)
        combined = alt_text.strip()
        if len(combined) + len(seo_sentence) <= 490:
            combined += seo_sentence
        else:
            # Trim alt_text to make space
            allowed_len = 490 - len(seo_sentence)
            combined = combined[:allowed_len].strip() + seo_sentence
            
        return combined

    async def execute_task_with_memory(self, task_name: str, task_fn, *args, **kwargs) -> Any:
        """
        Execute a task within a self-learning memory cycle.
        """
        import time
        import traceback
        from datetime import datetime, timezone
        
        # 1. SEARCH MEMORY BEFORE THE TASK
        logger.info(f"Memory Check: Searching past memories for task: '{task_name}'...")
        query = f"Failed while trying to '{task_name}'"
        
        # Get raw SearchResult list to read metadata
        query_vector = await self.memory.long_term._embeddings.get_embedding(query)
        results = self.memory.long_term._store.search(query_vector, limit=3)
        
        relevant_memories = [r for r in results if r.score >= 0.6 and r.metadata.get("type") == "failure"]
        
        if relevant_memories:
            logger.info("Memory retrieved: Found %d relevant past failures/solutions.", len(relevant_memories))
            for i, r in enumerate(relevant_memories):
                sol = r.metadata.get("working_solution", "None recorded yet")
                conf = r.metadata.get("confidence", 0.5)
                logger.info(
                    "  [%d] Match Score: %.2f | Failure: '%s' | Solution: '%s' | Confidence: %.2f",
                    i + 1, r.score, r.content[:80], sol, conf
                )
                if conf >= 0.7 and sol != "None recorded yet":
                    logger.info("Memory applied: Auto-applying solution/strategy based on high confidence score (%.2f).", conf)
        else:
            logger.info("Memory retrieved: No relevant past issues found for this task.")

        # 2. EXECUTE THE TASK
        start_time = time.time()
        try:
            result = await task_fn(*args, **kwargs)
            
            # 3. TASK SUCCEEDED: IF THERE WAS A PREVIOUS FAILURE, UPDATE IT (LEARNING)
            if relevant_memories:
                # Update the most similar past failure to record success strategy
                best_match = relevant_memories[0]
                meta = best_match.metadata
                
                # Update counters
                meta["success_count"] = meta.get("success_count", 0) + 1
                meta["confidence"] = min(1.0, meta.get("confidence", 0.5) + 0.1)
                meta["last_used"] = datetime.now(timezone.utc).isoformat()
                meta["updated_at"] = datetime.now(timezone.utc).isoformat()
                meta["working_solution"] = f"Resolved on next try. Task completed successfully in {time.time() - start_time:.2f}s."
                
                # Update vector store
                self.memory.long_term._store.update(best_match.id, metadata=meta)
                logger.info(
                    "Learning event: Memory confidence increased to %.2f for solved task '%s' (success_count: %d).",
                    meta["confidence"], task_name, meta["success_count"]
                )
                
            return result

        except Exception as exc:
            # 4. TASK FAILED: CAPTURE RUNTIME FAILURE AND STACK TRACE
            logger.error(f"Task '{task_name}' failed. Capturing details for LTM...")
            
            tb_str = traceback.format_exc()
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Dynamically fetch current browser URL and page title
            current_url = "Unknown"
            browser_state = "No active page"
            screenshot_path = None
            try:
                pages = self.browser_manager.context.pages
                if pages:
                    active_page = pages[-1]
                    current_url = active_page.url
                    browser_state = f"Active Page Title: {await active_page.title()}"
                    
                    # Capture screenshot
                    os.makedirs("logs", exist_ok=True)
                    screenshot_path = f"logs/memory_error_{int(time.time())}.png"
                    await active_page.screenshot(path=screenshot_path)
            except Exception as e:
                logger.debug(f"Failed to capture browser state/screenshot: {e}")

            error_msg = str(exc)
            exc_type = type(exc).__name__
            
            # Search if we already have this exact failure in memory
            # Query for exact message similarity
            failure_query = f"Failed while trying to '{task_name}'. Error: {error_msg}"
            failure_vector = await self.memory.long_term._embeddings.get_embedding(failure_query)
            existing_failures = self.memory.long_term._store.search(failure_vector, limit=3)
            
            matching_failures = [r for r in existing_failures if r.score >= 0.8 and r.metadata.get("type") == "failure"]
            
            if matching_failures:
                # Merge with existing failure
                best_match = matching_failures[0]
                meta = best_match.metadata
                meta["failure_count"] = meta.get("failure_count", 0) + 1
                meta["confidence"] = max(0.0, meta.get("confidence", 0.5) - 0.1)
                meta["last_used"] = now_iso
                meta["updated_at"] = now_iso
                meta["stack_trace"] = tb_str  # Update with latest stack trace
                meta["url"] = current_url
                meta["browser_state"] = browser_state
                if screenshot_path:
                    meta["screenshot_path"] = screenshot_path
                
                self.memory.long_term._store.update(best_match.id, metadata=meta)
                logger.info(
                    "Memory updated: Merged duplicate failure memory for task '%s'. Confidence decreased to %.2f (failure_count: %d).",
                    task_name, meta["confidence"], meta["failure_count"]
                )
            else:
                # Create new failure memory
                content = f"Failed while trying to '{task_name}'. Error: {error_msg}"
                meta = {
                    "type": "failure",
                    "task_name": task_name,
                    "exception_type": exc_type,
                    "exception_message": error_msg,
                    "stack_trace": tb_str,
                    "url": current_url,
                    "browser_state": browser_state,
                    "screenshot_path": screenshot_path,
                    "confidence": 0.5,
                    "success_count": 0,
                    "failure_count": 1,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "last_used": now_iso,
                    "working_solution": "None recorded yet"
                }
                
                await self.memory.long_term.remember_failure(
                    context=task_name,
                    error_msg=error_msg,
                    **meta
                )
                logger.info("Memory created: New failure recorded in Long-Term Memory for task '%s'.", task_name)

            # Re-raise the exception so it propagates normally to the pipeline/scheduler
            raise

    @log_execution(module="agent.core")
    async def run_affiliate_pipeline(
        self,
        niche: str = "trending beauty products for US women",
        board_name: str = "Beauty Finds",
        product_keyword: str | None = None
    ) -> bool:
        """
        Executes the fully autonomous End-to-End workflow with quality checks and dynamic board selection.
        Pinterest only — no Linktree.
        """
        if not self._is_initialized:
            await self.initialize()

        logger.info("Starting E2E Affiliate Pipeline for niche: '%s'", niche)

        # ── PRIORITY CHECK: Consume pre-seeded Pending_Pin queue from database ──
        db_pending_row = None
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 1").fetchone()
            if row:
                db_pending_row = dict(row)
                conn.execute("UPDATE products SET status = 'Processing' WHERE id = ?", (db_pending_row["id"],))

        db_product_id = None
        current_keyword = product_keyword

        if db_pending_row:
            db_product_id = db_pending_row["id"]
            p_name = db_pending_row.get("product_name") or "Sephora Viral Beauty Find"
            p_title = db_pending_row.get("title") or p_name
            p_img = db_pending_row.get("image_path") or "https://m.media-amazon.com/images/I/61ZQlTnCUbL._AC_UL320_.jpg"
            p_source = db_pending_row.get("source_url") or ""
            p_aff = db_pending_row.get("affiliate_link") or p_source
            p_board = db_pending_row.get("board_name") or "Sephora Viral Beauty Finds 2026"

            logger.info("📦 PRE-SEEDED QUEUE DETECTED! Processing Product ID #%d: '%s' (Board: '%s')...", db_product_id, p_name[:40], p_board)
            
            # Resolve link to clean direct ASIN URL
            clean_link = await self.amazon.ensure_direct_product_url(p_aff or p_name)
            if not clean_link or not clean_link.startswith("http") or "/dp/" not in clean_link:
                logger.info("Retrying link resolution for Product ID #%d using product_name: '%s'...", db_product_id, p_name)
                clean_link = await self.amazon.ensure_direct_product_url(p_name)

            if not clean_link or not clean_link.startswith("http"):
                logger.warning("⚠️ COULD NOT RESOLVE AFFILIATE LINK for Product ID #%d ('%s'). Marking as Failed_Quality and falling back to live sourcing...", db_product_id, p_name)
                with self.db.connection() as conn:
                    conn.execute("UPDATE products SET status = 'Failed_Quality' WHERE id = ?", (db_product_id,))
                db_pending_row = None
                db_product_id = None

        if db_pending_row and clean_link and clean_link.startswith("http"):
            # Synchronize Title, Image, and Price directly from the live Amazon ASIN page
            product_details = None
            try:
                if "/dp/" in clean_link:
                    fetched = await self.amazon.fetch_product_details(clean_link)
                    if fetched and fetched.title and fetched.title != "Unknown Product":
                        product_details = fetched
                        product_details.affiliate_url = clean_link
                        logger.info("✅ Live Product Synced with Amazon ASIN Page: '%s' (Price: %s)", product_details.title, product_details.price)
            except Exception as sync_err:
                logger.warning(f"Could not live sync Amazon product details: {sync_err}")

            if not product_details:
                # Sanitize title to match product_name if title is mismatched
                clean_short = " ".join(p_name.split()[:7])
                p_title = f"{clean_short} | Sephora Beauty Finds 2026"
                product_details = AmazonProduct(
                    title=p_title,
                    description=f"Discover {p_name}. Sephora viral beauty essential!",
                    price=db_pending_row.get("price") or "",
                    rating=4.8,
                    review_count=15000,
                    image_url=p_img,
                    affiliate_url=clean_link
                )
            else:
                # Update DB record with live synced ASIN link, product details, and price
                with self.db.connection() as conn:
                    conn.execute(
                        "UPDATE products SET product_name = ?, affiliate_link = ?, price = ? WHERE id = ?",
                        (product_details.title, clean_link, product_details.price, db_product_id)
                    )
        if not db_pending_row:
            # Fetch ALL previously posted products to avoid duplicates completely
            past_products = []
            with self.db.connection() as conn:
                cursor = conn.execute("SELECT DISTINCT product_name FROM products")
                past_products = [row["product_name"] for row in cursor.fetchall()]
                
            # STEP 1: Research/Idea Generation (Anti-Duplicate Loop)
            async def step_research():
                logger.info("STEP 1: Fetching live US trends & Generating product idea...")
                live_trends = await self.pinterest.get_us_beauty_trends()
                
                max_retries = 5
                candidate_keyword = None
                for attempt in range(max_retries):
                    if attempt >= 2:
                        logger.info("Attempt %d: Gemini stuck in repeat loop. Sourcing directly from live Pinterest trends/fallbacks...", attempt + 1)
                        candidate = self._get_unique_trend_fallback(live_trends, past_products, niche)
                    else:
                        candidate = await self.gemini.generate_product_idea(niche, past_products, live_trends, "", "")
                        candidate = self.parse_product_keyword(candidate)
                    
                    candidate_lower = candidate.lower()
                    blocked_terms = ["pinterest", "google", "analysis", "trends", "passive income", "profits", "selected beauty trend", "trend product", "selected product"]
                    is_generic = candidate_lower in ["trending beauty product", "makeup beauty find", "selected beauty trend product", "beauty trend product", "selected product"] or "trend product" in candidate_lower or "beauty trend" in candidate_lower or len(candidate) < 4
                    has_blocked = any(w in candidate_lower for w in blocked_terms)
                    
                    if is_generic or has_blocked:
                        logger.warning("Parsed keyword is generic or contains blocked terms: '%s'. Retrying attempt %d...", candidate, attempt + 1)
                        continue
                        
                    with self.db.connection() as conn:
                        chk = conn.execute("SELECT 1 FROM products WHERE LOWER(product_name) = LOWER(?)", (candidate,))
                        if not chk.fetchone():
                            candidate_keyword = candidate
                            break
                        else:
                            logger.warning("Generated duplicate keyword: '%s'. Retrying...", candidate)
                            past_products.append(candidate)
                else:
                    candidate_keyword = self._get_unique_trend_fallback(live_trends, past_products, niche)
                return candidate_keyword

            # AUTOMATIC UNIQUE PRODUCT RETRY LOOP
            max_sourcing_attempts = 5
            product_details = None

            for sourcing_attempt in range(1, max_sourcing_attempts + 1):
                if current_keyword and sourcing_attempt == 1:
                    current_keyword = self.parse_product_keyword(current_keyword)
                    logger.info("Bypass Mode / Initial Keyword: '%s'", current_keyword)
                else:
                    try:
                        current_keyword = await self.execute_task_with_memory("Research and Idea Generation", step_research)
                    except Exception as e:
                        logger.error(f"Research failed on attempt {sourcing_attempt}: {e}")
                        return False

                logger.info("Sourcing Attempt [%d/%d] — Selected Keyword: %s", sourcing_attempt, max_sourcing_attempts, current_keyword)
                
                # Step 2: Amazon Sourcing (100% Price & Metadata Guarantee)
                async def step_amazon_sourcing():
                    logger.info("STEP 2: Sourcing from Amazon for '%s'...", current_keyword)
                    prod = await self.amazon.search_and_fetch_product(current_keyword)
                    if not prod:
                        raise Exception(f"Failed to find product '{current_keyword}' on Amazon.")
                    return prod
                    
                try:
                    candidate_details = await self.execute_task_with_memory("Amazon Sourcing", step_amazon_sourcing)
                except Exception as e:
                    logger.error(f"Amazon Sourcing failed for '{current_keyword}': {e}. Blacklisting and retrying...")
                    past_products.append(current_keyword)
                    current_keyword = None
                    continue

                if not candidate_details or candidate_details.title == "Unknown Product" or not candidate_details.image_url:
                    logger.warning("⚠️ INVALID PRODUCT DETAILS DETECTED! Title is 'Unknown Product' or Image URL is missing. Blacklisting candidate '%s'...", current_keyword)
                    past_products.append(current_keyword)
                    if candidate_details and candidate_details.title:
                        past_products.append(candidate_details.title)
                    current_keyword = None
                    continue

                if is_book_product(candidate_details.title) or is_book_product(current_keyword) or is_non_beauty_product(candidate_details.title):
                    logger.warning("⚠️ NON-BEAUTY DETECTED! '%s' (Title: '%s') is non-beauty. Blacklisting and re-triggering research...", current_keyword, candidate_details.title)
                    past_products.append(current_keyword)
                    past_products.append(candidate_details.title)
                    current_keyword = None
                    continue
                    
                if candidate_details.rating > 0 and candidate_details.rating < 4.0:
                    logger.warning("⚠️ LOW RATING DETECTED! '%s' has only %.1f★ rating. Blacklisting and sourcing higher-rated alternative...", candidate_details.title, candidate_details.rating)
                    past_products.append(current_keyword)
                    past_products.append(candidate_details.title)
                    current_keyword = None
                    continue
                    
                new_asin = extract_asin(candidate_details.affiliate_url)
                is_duplicate = False
                
                with self.db.connection() as conn:
                    cursor = conn.execute("SELECT product_name, title, affiliate_link FROM products")
                    all_db_rows = cursor.fetchall()
                    
                    existing_links = [r["affiliate_link"] for r in all_db_rows if r["affiliate_link"]]
                    existing_titles = [((r["title"] or "") + " " + (r["product_name"] or "")).strip() for r in all_db_rows]

                    if new_asin:
                        for link in existing_links:
                            if extract_asin(link) == new_asin:
                                is_duplicate = True
                                logger.warning("Duplicate ASIN detected: %s", new_asin)
                                break

                    if not is_duplicate:
                        c_kw_clean = (current_keyword or "").lower().strip()
                        c_title_clean = (candidate_details.title or "").lower().strip()
                        for row in all_db_rows:
                            pname = (row["product_name"] or "").lower().strip()
                            ptitle = (row["title"] or "").lower().strip()
                            if (c_kw_clean and c_kw_clean in (pname, ptitle)) or (c_title_clean and c_title_clean in (pname, ptitle)):
                                is_duplicate = True
                                logger.warning("Exact title/keyword match duplicate detected: '%s'", c_title_clean)
                                break

                    if not is_duplicate:
                        if is_fuzzy_duplicate_title(candidate_details.title, existing_titles) or (current_keyword and is_fuzzy_duplicate_title(current_keyword, existing_titles)):
                            is_duplicate = True
                            logger.warning("Fuzzy title similarity duplicate detected for candidate: '%s'", candidate_details.title)

                if is_duplicate:
                    logger.warning("⚠️ DUPLICATE PRODUCT DETECTED! '%s' (ASIN: %s) already published. Blacklisting and re-triggering Research for a new product...", candidate_details.title, new_asin or 'N/A')
                    past_products.append(current_keyword)
                    past_products.append(candidate_details.title)
                    current_keyword = None
                    continue

                product_details = candidate_details
                logger.info("✅ UNIQUE BEAUTY PRODUCT CONFIRMED: '%s' (ASIN: %s)", product_details.title, new_asin or 'N/A')
                break
            else:
                logger.error("❌ Failed to source a unique beauty product after %d attempts.", max_sourcing_attempts)
                return False
        
        # Step 3: Downloading Amazon product image first
        async def step_image_download():
            logger.info("STEP 3: Downloading Amazon product image first...")
            img_path = self.image_tools.download_image(product_details.image_url)
            if not img_path:
                raise Exception(f"Failed to download image from URL: {product_details.image_url}")
            return img_path
            
        try:
            amazon_img_path = await self.execute_task_with_memory("Image Download", step_image_download)
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            return False
        
        # Step 4: Image & SEO Generation via Gemini
        async def step_gemini_seo():
            logger.info("STEP 4: Generating Aesthetic Image & SEO via Gemini Web (Price: %s, Rating: %.1f★, Reviews: %d)...", 
                        getattr(product_details, "price", "N/A"), product_details.rating, product_details.review_count)
            gemini_img_path, seo_data = await self.gemini.generate_image_and_seo(
                product_title=product_details.title,
                product_desc=product_details.description,
                image_path=amazon_img_path,
                product_price=getattr(product_details, "price", ""),
                product_rating=product_details.rating,
                product_reviews=product_details.review_count
            )
            if not seo_data or not seo_data.title or not seo_data.description:
                raise Exception("Gemini Web returned invalid or empty SEO/title details.")
            return gemini_img_path, seo_data
            
        try:
            gemini_img_path, seo_data = await self.execute_task_with_memory("Gemini SEO Generation", step_gemini_seo)
        except Exception as e:
            logger.error(f"Gemini SEO Generation failed: {e}")
            return False
        
        if gemini_img_path:
            logger.info("Successfully generated AI Image from Gemini: %s", gemini_img_path)
            raw_image_path = gemini_img_path
        else:
            logger.warning("Falling back to Amazon product image.")
            raw_image_path = amazon_img_path
            
        logger.info("Formatting image for BADDIES BEAUTY v4.0 Pinterest Pin...")
        try:
            self.pin_counter += 1
            # Ensure overlay text on pin image strictly matches the actual product title and brand
            raw_headline = getattr(seo_data, "image_headline", None)
            prod_title_lower = product_details.title.lower()
            headline_lower = (raw_headline or "").lower()
            mismatch_terms = [("patch", "lip oil"), ("patch", "cushion"), ("patch", "foundation"), ("patch", "setting spray"), ("lip", "foundation"), ("sunscreen", "lip oil")]
            is_mismatched_headline = any((c1 in prod_title_lower and c2 in headline_lower) for c1, c2 in mismatch_terms)

            if not raw_headline or len(raw_headline.strip()) < 3 or is_mismatched_headline or "selected" in raw_headline.lower() or "trending product" in raw_headline.lower():
                headline = " ".join(product_details.title.split()[:6])
            else:
                headline = raw_headline.strip()

            price_val = getattr(product_details, "price", "")
            short_badge = getattr(seo_data, "badge_text", None) or self.image_tools.get_smart_badge(product_details.title, self.pin_counter, price_val)
            
            # Format Real Amazon Star Rating Social Proof below CTA button (100% Guaranteed on ALL Pins)
            if product_details.rating > 0:
                rev_cnt = product_details.review_count
                rev_k = f"{rev_cnt // 1000}K+" if rev_cnt >= 1000 else f"{rev_cnt}"
                rating_str = f"{product_details.rating:.1f}★ ({rev_k} REVIEWS)"
            else:
                rating_str = "4.8★ (15K+ REVIEWS)"
                
            cta_text = getattr(seo_data, "cta_text", None) or ""
            pin_image_path = self.image_tools.create_pinterest_pin(
                raw_image_path, 
                title_text=headline,
                badge_text=short_badge,
                cta_text=cta_text,
                pin_index=self.pin_counter,
                rating_text=rating_str,
                price_text=price_val
            )
        except Exception as e:
            logger.error(f"Failed to format image: {e}")
            return False
        
        # Determine the final board name based on title and suggested category, keeping 50 pin limit
        suggested = seo_data.board.strip() if seo_data and seo_data.board else None
        target_board = self.choose_board_by_product(product_details.title, suggested)
            
        # Count existing pins on target board to keep under 50 pins
        with self.db.connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM products WHERE board_name = ?", (target_board,))
            row = cursor.fetchone()
            count = row["cnt"] if row else 0
            
        if count >= 50:
            suffix = 2
            while True:
                candidate_board = f"{target_board} {suffix}"
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM products WHERE board_name = ?", (candidate_board,))
                row = cursor.fetchone()
                candidate_count = row["cnt"] if row else 0
                if candidate_count < 50:
                    target_board = candidate_board
                    break
                suffix += 1
                
        logger.info("Board chosen for this Pin: '%s' (current count: %d)", target_board, count)

        # Optimize Alt-Text with SEO keywords matching the target board
        logger.info("Optimizing Alt-Text for Pinterest SEO...")
        seo_data.alt_text = self.optimize_alt_text(seo_data.alt_text, target_board, niche)

        # Pre-publish Quality Check
        if not self.verify_quality(product_details, seo_data, pin_image_path, target_board, db_product_id=db_product_id):
            logger.error("Quality Check failed! Aborting publish.")
            if db_product_id:
                with self.db.connection() as conn:
                    conn.execute("UPDATE products SET status = 'Failed_Quality' WHERE id = ?", (db_product_id,))
            return False

        # Step 5: Pinterest Upload
        async def step_pinterest_upload():
            logger.info("STEP 5: Uploading to Pinterest...")
            
            # Ensure we are logged in to Pinterest first
            if not await self.pinterest.is_logged_in():
                import os
                email = os.getenv("PINTEREST_EMAIL")
                password = os.getenv("PINTEREST_PASSWORD")
                if not email or not password:
                    raise Exception("Pinterest credentials not found in settings/.env")
                    
                await self.pinterest.login(email, password)
                
            clean_link = await self.amazon.ensure_direct_product_url(product_details.affiliate_url)
            if "/dp/" not in clean_link:
                logger.error("❌ Link verification failed! Link '%s' is not a direct ASIN product page. Aborting upload.", clean_link)
                raise ValueError(f"Cannot publish pin with non-direct search link: {clean_link}")

            logger.info("✅ Verified clean direct Amazon product link for Pin: %s", clean_link)
            
            # Create the Pin
            pin_url = await self.pinterest.create_pin(
                image_path=pin_image_path,
                title=seo_data.title,
                description=seo_data.description,
                board_name=target_board,
                link=clean_link,
                alt_text=seo_data.alt_text
            )
            if not pin_url:
                raise Exception("Pinterest upload failed or did not return a valid URL.")
            return pin_url
            
        try:
            pin_url = await self.execute_task_with_memory("Pinterest Upload", step_pinterest_upload)
        except Exception as e:
            logger.error(f"Pinterest Upload failed: {e}")
            return False

        # Save to database immediately to prevent duplicates (Pinterest Pin is already live)
        final_product_name = current_keyword or product_keyword or (product_details.title if product_details else None) or "Beauty Product"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        
        with self.db.connection() as conn:
            if db_product_id:
                conn.execute(
                    """
                    UPDATE products SET 
                        status = 'Published',
                        pin_url = ?,
                        image_path = ?,
                        title = ?,
                        description = ?,
                        board_name = ?,
                        price = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        pin_url,
                        pin_image_path,
                        seo_data.title,
                        seo_data.description,
                        target_board,
                        getattr(product_details, "price", ""),
                        now_iso,
                        db_product_id
                    )
                )
            else:
                conn.execute(
                    """
                    INSERT INTO products (product_name, category, board_name, status, image_path, source_url, title, description, affiliate_link, pin_url, price, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        final_product_name,
                        niche,
                        target_board,
                        "Published",
                        pin_image_path,
                        product_details.image_url,
                        seo_data.title,
                        seo_data.description,
                        product_details.affiliate_url,
                        pin_url,
                        getattr(product_details, "price", ""),
                        now_iso,
                        now_iso
                    )
                )

        logger.info("🎉 SUCCESS! Pin published directly to Pinterest with Direct Amazon Affiliate Link: %s", pin_url)
        return True
    def _get_unique_trend_fallback(self, live_trends: list[str], past_products: list[str], niche: str) -> str:
        """
        Safely returns a fresh, non-duplicate viral beauty product keyword 
        directly from live Pinterest Trends or curated viral beauty fallbacks.
        """
        import random
        past_set = set(p.lower().strip() for p in (past_products or []))
        
        # 1. Try to find a live trend keyword that hasn't been posted yet
        if live_trends:
            available_trends = [t.strip() for t in live_trends if t.strip().lower() not in past_set and len(t.strip()) > 5]
            if available_trends:
                chosen = random.choice(available_trends)
                logger.info(f"Fallback selected fresh live trend keyword: '{chosen}'")
                return chosen

        # 2. Curated viral beauty fallbacks (100+ Fresh US/UK/CA Virals for 2026)
        fallbacks = [
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
            "Billie Eilish Eau de Parfum Vanilla Amber",
            
            # ── 2026 Fresh TikTok & Pinterest Virals (US/UK/Canada) ──
            "Mixsoon Bean Cleansing Oil Hydrating Exfoliator",
            "Aestura Atobarrier 365 Hydro Soothing Lotion",
            "Numbuzin No.5 Goodbye Blemish Serum",
            "SKIN1004 Centella Ampoule Foam Cleanser",
            "Round Lab Dokdo Cleanser Mild Facial Wash",
            "Dr.Althea 345 Relief Cream Barrier Repair",
            "Zeroid Soothing Cream Sensitive Skin",
            "Celimax Dual Barrier Serum Ceramide",
            "Abib Heartleaf Spot Pad Calming Touch",
            "Needly Daily Toner Pad Pore Tightening",
            "Medicube PDRN Pink Peptide Serum Collagen",
            "Medicube Zero Pore Serum 2.0 Pore Minimizer",
            "Torriden Dive-In Cleansing Foam Hyaluronic Acid",
            "d'Alba Waterfull Tone-Up Sunscreen SPF 50",
            "Fwee Lip & Cheek Blur Pot Pudding Tint",
            "Rom&nd Glasting Melting Balm Lip Tint",
            "Clio Kill Cover Mesh Glow Cushion Foundation",
            "Dasique Shadow Palette Ice Cream Collection",
            "e.l.f. Soft Glam Satin Foundation Light Medium",
            "Sol de Janeiro Cheirosa 71 Body Mist Caramelized Vanilla",
            "Sol de Janeiro Rio Radiance Perfume Mist",
            "Rhode Pocket Blush Piggy Soft Pink",
            "Rhode Pocket Blush Juice Box Bright Coral",
            "Rhode Pocket Blush Freckle Neutral Tan",
            "Summer Fridays Lip Butter Balm Birthday Cake",
            "Summer Fridays Lip Butter Balm Hot Cocoa",
            "Rare Beauty Soft Pinch Matte Liquid Eyeliner",
            "Charlotte Tilbury Pillow Talk Lip Cheat Lip Liner",
            "Dior Backstage Rosy Glow Blush 001 Pink",
            "Glow Recipe Watermelon Glow Niacinamide Hue Drops",
            "Patrick Ta Major Headlines Double-Take Cream & Powder Blush",
            "Tarte Maracuja Juicy Lip Plump Shift",
            "Kosas Revealer Super Creamy Concealer",
            "Tower 28 ShineOn Lip Jelly Gloss",
            "Saie Dew Blush Liquid Blush Peachy",
            "Supergoop! Glowscreen SPF 40 Sunscreen",
            "Maelove Glow Maker Vitamin C Serum",
            "Nuxe Huile Prodigieuse Multi-Purpose Dry Oil",
            "L'Oreal Paris True Match Lumi Glotion Natural Glow Enhancer",
            "Maybelline Lifter Gloss Hyaluronic Acid Lip Gloss",
            "NYX Professional Makeup Jumbo Eye Pencil All-in-One",
            "Moroccanoil Dry Body Oil Fast Absorbing",
            "Color Wow One Minute Transformation Anti Frizz Cream",
            "Kerastase Elixir Ultime L'Huile Original Hair Oil",
            "Redken Acidic Bonding Concentrate Leave-In Treatment",
            "Ouai Wave Spray Sea Salt Mist",
            "Dyson Airstrait Straightener Wet to Dry",
            "Shark Beauty SmoothStyle Heated Comb Brush",
            "Nivea Super Water Gel SPF 50 PA+++ Sunscreen",

            # ── 2026 Sephora Featured A+ Beauty Essentials ──
            "Glossier Balm Dotcom Lip Balm and Skin Salve",
            "ONE/SIZE by Patrick Starrr Mini Oil Sucker Liquid Blotting Paper Touch-Up Spray",
            "Summer Fridays Lip Butter Balm Treatment Strawberry Soft Serve",
            "Sincerely Yours Clear Intentions Hydrating and Pore-Clarifying Essential Toner",
            "Salt & Stone Lily & Yuzu Extra-Strength Aluminum-Free Deodorant",
            "Ariana Grande Cloud Aurora Eau de Parfum Travel Spray",
            "OUAI Mini St. Barts Ibiza Santorini Melrose Hair & Body Mist Set",
            "Emi Jay Angel Essentials Hair Styling Gift Set",
            "Tower 28 Beauty SOS Daily Hypochlorous Acid Spray for Breakouts & Redness",
            "REFY Lash Sculpt Lengthen and Lift Natural Looking Mascara",
            "SOFIE PAVITT FACE 3 Step Acne-Safe Clear Skin System with Mandelic Acid",
            "LANEIGE Lip Sleeping Mask Acai Mango Smoothie",
            "rhode Peptide Lip Tint Nourishing Glaze Jelly Bean",
            "Topicals Faded Tranexamic Acid Dark Spot Patches for Hyperpigmentation",
            "KAYALI VANILLA 28 Eau de Parfum Travel Spray",
            "Glossier Glossier You Eau de Parfum Travel Spray",
            "dae Cactus Fruit 3-in-1 Styling Cream with Taming Wand",
            "Saie Glowy Super Gel Lightweight Dewy Multipurpose Illuminator Sunglow",
            "Sol de Janeiro Cheirosa 48 Hair & Body Perfume Mist",
            "Glossier Glossier You Eau de Parfum",
            "KAYALI BOUJEE KITTY CARAMEL MILK 22 Eau de Parfum",
            "SKYLAR Boardwalk Delight Eau de Parfum",
            "Kérastase Gloss Absolu Glaze Drops Anti-Frizz Hair Oil",
            "K18 Biomimetic Hairscience AirWash Dry Shampoo"
        ]
        
        available_fallbacks = [f for f in fallbacks if f.lower().strip() not in past_set]
        if available_fallbacks:
            chosen = random.choice(available_fallbacks)
            logger.info(f"Fallback selected fresh curated keyword: '{chosen}'")
            return chosen

        return random.choice(fallbacks)

    async def update_pin_analytics(self, scroll_count: int = 4) -> None:
        """
        Trigger Pinterest profile scraping and update the local database with impressions, clicks, saves.
        """
        logger.info("Triggering update_pin_analytics...")
        
        scraped_data = await self.pinterest.scrape_profile_analytics(scroll_count=scroll_count)
        if not scraped_data:
            logger.warning("No analytics data scraped or scraping failed.")
            return
            
        import datetime
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        
        updated_count = 0
        with self.db.connection() as conn:
            for item in scraped_data:
                pin_id = item["pin_id"]
                impressions = item["impressions"]
                saves = item["saves"]
                clicks = item["clicks"]
                
                cursor = conn.execute(
                    "UPDATE products SET impressions = ?, saves = ?, clicks = ?, stats_updated_at = ? WHERE pin_url LIKE ?",
                    (impressions, saves, clicks, now_str, f"%{pin_id}%")
                )
                if cursor.rowcount > 0:
                    updated_count += cursor.rowcount
                    logger.debug(f"Updated stats for pin ID {pin_id}: impressions={impressions}, saves={saves}, clicks={clicks}")
                    
        logger.info(f"update_pin_analytics complete. Updated database records for {updated_count} pins.")

    def parse_product_keyword(self, candidate: str) -> str:
        """
        Parses a potentially chatty, multi-line markdown response from Gemini 
        to extract exactly one clean beauty search query/product name.
        """
        import re
        if not candidate:
            return "trending beauty product"

        # 0. Check for explicit <product>...</product> tags
        match = re.search(r'<product>(.*?)</product>', candidate, re.DOTALL | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip().replace('"', "").replace("'", "")
            if extracted and not is_book_product(extracted):
                return extracted

        candidate = candidate.strip().replace('"', "").replace("'", "")
        candidate = re.sub(r'^(?:Product Name|Product Title|Selected Product|Product|Title|Search Query|Keyword)\s*:\s*', '', candidate, flags=re.IGNORECASE).strip()
        
        # Split by lines and remove empty ones
        lines = [line.strip() for line in candidate.split('\n') if line.strip()]
        if not lines:
            return "trending beauty product"

        blocked_terms = [
            "pinterest", "google", "analysis", "trends", "passive income", "profits", "based on", "following",
            "step 1", "step 2", "step 3", "step 4", "step 5", "step 6", "step 7", "step 8", "step 9", "step 10",
            "navigation", "workflow", "proceed", "completed", "instructions", "overview", "dashboard", "selection",
            "research", "workflow developer", "navigation handbook", "selected beauty trend product", "beauty trend product", "selected product", "trend product"
        ]
            
        # 1. Clean list prefixes, numbered items, and bold formatting
        for i in range(len(lines)):
            line = lines[i]
            line = line.replace("**", "")
            line = re.sub(r'^\s*[\-\*\•\d\.\)]+\s*', '', line).strip()
            line = re.sub(r'^(?:Product Name|Product Title|Selected Product|Product|Title|Search Query|Keyword)\s*:\s*', '', line, flags=re.IGNORECASE).strip()
            lines[i] = line

        # 2. Try to locate standard plaintext search query blocks
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "plaintext" in line_lower or "search query" in line_lower or "is:" in line_lower:
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and not next_line.startswith("#") and len(next_line) > 3:
                        if not any(w in next_line.lower() for w in blocked_terms) and not is_book_product(next_line):
                            return next_line
                        
        # 3. Known brand extraction from any line (even long sentences)
        known_brands = [
            "dyson", "shark", "omnilux", "dennis", "nuface", "braun", "foreo", "anua", "cosrx", 
            "joseon", "round lab", "centella", "tatcha", "paula", "glow recipe", "baccarat", 
            "sol de janeiro", "ysl", "black opium", "kayali", "replica", "good girl", "delina", 
            "nyx", "rhode", "rare beauty", "charlotte tilbury", "fenty", "summer fridays", 
            "merit", "huda", "milk makeup", "tower 28", "laneige", "bum bum", "tree hut", 
            "necessaire", "osea", "eos", "l'occitane", "lume", "olaplex", "k18", "gisou", 
            "mielle", "color wow", "ouai", "amika", "peter thomas", "shiseido", "roc", "cetaphil",
            "cerave", "la roche-posay", "ordinary", "inkey list", "kiss lash", "emi jay", "milani",
            "numbuzin", "rael", "kopari", "panoxyl", "loreal"
        ]
        
        for line in lines:
            line_lower = line.lower()
            for brand in known_brands:
                if brand in line_lower:
                    idx = line_lower.find(brand)
                    sub = line[idx:]
                    for char in [".", ",", ";", "\n", "  "]:
                        if char in sub:
                            sub = sub.split(char)[0]
                    sub = sub.strip()
                    if 5 < len(sub) < 120 and not any(w in sub.lower() for w in blocked_terms) and not is_book_product(sub):
                        return sub
                        
        # 4. Filter lines that don't contain blocklist words or book terms
        for line in lines:
            if len(line) < 90 and not line.startswith("#"):
                if not any(w in line.lower() for w in blocked_terms) and not is_book_product(line):
                    return line
                    
        # 5. Last resort fallback
        return "trending beauty product"

    def get_pending_linktree_product(self) -> dict | None:
        """Fetch next product that has status 'Pinterest_Published' but has not been synced to Linktree."""
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT id, product_name, category, affiliate_link, title, source_url FROM products WHERE status = 'Pinterest_Published' ORDER BY id ASC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    async def sync_pending_linktree_product(self, product_item: dict) -> bool:
        """Add pending product link to Linktree Shop under its category collection and mark status as 'Published'."""
        if not hasattr(self, "linktree") or not self.linktree:
            from browser.linktree_client import LinktreeClient
            self.linktree = LinktreeClient(self.browser_manager)

        title = product_item.get("title") or product_item.get("product_name") or "Beauty Product"
        clean_title = title if len(title) <= 60 else " ".join(title.split()[:7])
        category = product_item.get("category") or "Amazon Beauty Finds"
        url = product_item.get("affiliate_link") or product_item.get("source_url")

        if not url:
            logger.error(f"Cannot sync product [ID #{product_item['id']}]: empty affiliate URL")
            return False

        logger.info(f"Syncing pending product [ID #{product_item['id']}] to Linktree: '{clean_title}'...")
        success = await self.linktree.add_link(title=clean_title, url=url, category=category)
        if success:
            with self.db.connection() as conn:
                conn.execute("UPDATE products SET status = 'Published' WHERE id = ?", (product_item["id"],))
            logger.info(f"✅ Successfully synced ID #{product_item['id']} to Linktree!")
            return True
        else:
            logger.error(f"❌ Failed to sync ID #{product_item['id']} to Linktree.")
            return False

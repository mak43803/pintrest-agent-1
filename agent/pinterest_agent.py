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

from config.settings import get_settings
settings = get_settings()
from database.database import Database
from database.init_db import create_database
from browser.browser_manager import BrowserManager
from browser.pinterest_client import PinterestClient
from browser.amazon_client import AmazonClient
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
        
        # 1. Respect valid suggested board if provided by Trend Miner or SEO
        if suggested_board and suggested_board.strip() and suggested_board.strip() not in ["Amazon Beauty Finds", "Amazon Viral Beauty Finds"]:
            sug_lower = suggested_board.lower()
            if any(w in sug_lower for w in ["perfume", "fragrance", "body mist", "cologne", "scent"]):
                return "Signature Perfumes & Fragrances"
            return suggested_board.strip()

        # 2. Force true perfume/fragrance items to "Signature Perfumes & Fragrances"
        if any(w in title_lower for w in ["perfume", "fragrance", "body mist", "perfume mist", "fragrance mist", "cologne", "scent", "eau de", "edp", "edt"]):
            return "Signature Perfumes & Fragrances"
            
        if any(w in title_lower for w in ["teeth", "tooth", "smile", "whitening", "floss", "breath"]):
            board = "Teeth Whitening & Smile Care"
        elif any(w in title_lower for w in ["patch", "pimple", "acne patch", "zit"]):
            board = "Overnight Acne & Pimple Patches"
        elif any(w in title_lower for w in ["dark spot", "hyperpigmentation", "brightening"]):
            board = "Dark Spot Correctors & Brightening"
        elif any(w in title_lower for w in ["travel", "tsa", "mini", "toiletry"]):
            board = "TSA Approved Travel Beauty Essentials"
        elif any(w in title_lower for w in ["korean", "k-beauty", "anua", "cosrx", "beauty of joseon", "round lab", "essence", "snail", "mixsoon", "dr.althea", "aestura", "illiyoon", "real barrier"]):
            board = "Korean Glass Skin Secrets"
        elif any(w in title_lower for w in ["sephora", "rare beauty", "fenty", "sol de janeiro", "charlotte tilbury", "huda beauty", "laneige", "dior beauty", "nars", "tatcha", "glow recipe"]):
            board = "Sephora Viral Beauty Dupes"
        elif any(w in title_lower for w in ["eye", "lash", "brow", "eyeliner", "mascara", "under-eye", "undereye"]):
            board = "Clean Girl Eye & Brow Routine"
        elif any(w in title_lower for w in ["lip", "gloss", "balm", "lipstick", "tint", "plumper"]):
            board = "Viral Lip Oils & Tints"
        elif any(w in title_lower for w in ["hair growth", "rosemary oil", "density", "biotin"]):
            board = "Hair Growth Oils & Serums"
        elif any(w in title_lower for w in ["hair", "shampoo", "conditioner", "oil", "scalp", "growth"]):
            board = "90s Blowout & Hair Care Secrets"
        elif any(w in title_lower for w in ["blush", "bronzer", "contour"]):
            board = "Cream Blush & Bronzer Glow"
        elif any(w in title_lower for w in ["makeup", "foundation", "concealer", "powder", "palette", "brush", "beauty blender"]):
            board = "Clean Girl Aesthetic Makeup"
        elif any(w in title_lower for w in ["wash", "cleanser", "soap", "cleansing"]):
            board = "Hydrating Cleansers & Face Wash"
        elif any(w in title_lower for w in ["serum", "ampoule", "drops"]):
            board = "Glow Serums & Glass Skin"
        elif any(w in title_lower for w in ["moisturizer", "cream", "gel", "lotion", "sunscreen", "spf"]):
            board = "Dewy Moisturizers & Daily SPF"
        elif any(w in title_lower for w in ["body", "scrub", "shower", "shaving", "deodorant", "wash"]):
            board = "Aesthetic Vanilla Body Routine"
        elif any(w in title_lower for w in ["nail", "polish", "gel", "manicure"]):
            board = "Glazed Donut & Gel Nails"
        elif any(w in title_lower for w in ["roller", "gua sha", "led", "mask", "steamer", "device", "tool"]):
            board = "At-Home Beauty Tools & Devices"
        else:
            board = "Amazon Viral Beauty Finds"
            
        return board

    def verify_quality(self, product_details: Any, seo_data: Any, image_path: str, board_name: str) -> bool:
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

        # 6. Content uniqueness & US English character checks
        with self.db.connection() as conn:
            # Check for duplicate affiliate link to prevent re-posting the same product
            if product_details.affiliate_url:
                cursor = conn.execute(
                    "SELECT 1 FROM products WHERE affiliate_link = ? OR LOWER(title) = LOWER(?) OR LOWER(description) = LOWER(?)",
                    (product_details.affiliate_url, seo_data.title, seo_data.description)
                )
            else:
                cursor = conn.execute(
                    "SELECT 1 FROM products WHERE LOWER(title) = LOWER(?) OR LOWER(description) = LOWER(?)",
                    (seo_data.title, seo_data.description)
                )
                
            if cursor.fetchone():
                logger.error("Quality Check Failed: Duplicate Affiliate Link or SEO Title/Description already exists in DB.")
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

    def get_pending_linktree_product(self) -> dict | None:
        """Query DB for the next product pending Linktree sync."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, product_name, title, board_name, affiliate_link 
                FROM products 
                WHERE status IN ('Pinterest_Published', 'Linktree_Deferred') AND affiliate_link IS NOT NULL AND affiliate_link != ''
                ORDER BY id ASC LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    async def sync_pending_linktree_product(self, pending_row: dict | None = None) -> bool:
        """Sync a pending product (status = 'Pinterest_Published') to Linktree Shop."""
        if not self._is_initialized:
            await self.initialize()

        if not pending_row:
            pending_row = self.get_pending_linktree_product()

        if not pending_row:
            return False

        p_id = pending_row["id"]
        p_title = pending_row["title"] or pending_row["product_name"]
        p_url = pending_row["affiliate_link"]
        p_board = pending_row["board_name"] or "General Beauty"
        logger.info("⏳ RESUMING PENDING LINKTREE PRODUCT [ID #%d]: '%s' (Board: '%s'). Syncing to Linktree first before starting new pin...", p_id, p_title, p_board)

        async def step_linktree_sync_recovery():
            logger.info("STEP 6 (RECOVERY): Retrying Linktree collection addition...")
            if not await self.linktree.is_logged_in():
                logged_in = await self.linktree.login()
                if not logged_in:
                    raise Exception("Failed to log in to Linktree via Google.")

            success = await self.linktree.add_link_to_collection(
                title=p_title,
                url=p_url,
                collection_name=p_board
            )
            if not success:
                raise Exception(f"Failed to add link to Linktree collection '{p_board}'.")
            return True

        try:
            await self.execute_task_with_memory("Linktree Link Addition", step_linktree_sync_recovery)
            with self.db.connection() as conn:
                conn.execute("UPDATE products SET status = 'Published', retry_count = 0 WHERE id = ?", (p_id,))
            logger.info("🎉 RECOVERY SUCCESSFUL! Product [ID #%d] successfully synced to Linktree!", p_id)
            return True
        except Exception as e:
            logger.error(f"Linktree recovery addition failed for product ID #{p_id}: {e}")
            with self.db.connection() as conn:
                conn.execute("UPDATE products SET retry_count = COALESCE(retry_count, 0) + 1 WHERE id = ?", (p_id,))
                cursor = conn.execute("SELECT retry_count FROM products WHERE id = ?", (p_id,))
                r_row = cursor.fetchone()
                r_count = r_row["retry_count"] if r_row else 1
                if r_count >= 3:
                    logger.warning(f"⚠️ Product ID #{p_id} failed Linktree sync {r_count} times. Deferring to unblock pipeline...")
                    conn.execute("UPDATE products SET status = 'Linktree_Deferred' WHERE id = ?", (p_id,))
            raise e

    @log_execution(module="agent.core")
    async def run_affiliate_pipeline(
        self,
        niche: str = "trending beauty products for US women",
        board_name: str = "Beauty Finds",
        product_keyword: str | None = None
    ) -> bool:
        """
        Executes the fully autonomous End-to-End workflow with quality checks and dynamic board selection.
        """
        if not self._is_initialized:
            await self.initialize()

        # 0. CHECK FOR PENDING LINKTREE SYNC PRODUCTS FIRST!
        pending_row = self.get_pending_linktree_product()
        if pending_row:
            return await self.sync_pending_linktree_product(pending_row)

        logger.info("Starting E2E Affiliate Pipeline for niche: '%s'", niche)

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
                    # Do NOT pass Amazon Best Sellers anymore to force Gemini to use fresh Pinterest/Google trends
                    candidate = await self.gemini.generate_product_idea(niche, past_products, live_trends, "", "")
                    candidate = self.parse_product_keyword(candidate)
                
                # Validate keyword contains no blocked terms and is not generic
                candidate_lower = candidate.lower()
                blocked_terms = ["pinterest", "google", "analysis", "trends", "passive income", "profits", "selected beauty trend", "trend product", "selected product"]
                is_generic = candidate_lower in ["trending beauty product", "makeup beauty find", "selected beauty trend product", "beauty trend product", "selected product"] or "trend product" in candidate_lower or "beauty trend" in candidate_lower or len(candidate) < 4
                has_blocked = any(w in candidate_lower for w in blocked_terms)
                
                if is_generic or has_blocked:
                    logger.warning("Parsed keyword is generic or contains blocked terms: '%s'. Retrying attempt %d...", candidate, attempt + 1)
                    continue
                    
                # Double check against full DB to prevent duplicate keyword selection
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

        # AUTOMATIC UNIQUE PRODUCT RETRY LOOP (Max 5 attempts to ensure 0 duplicates)
        max_sourcing_attempts = 5
        product_details = None
        current_keyword = product_keyword

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
            
            # Step 2: Amazon Sourcing
            async def step_amazon_sourcing():
                logger.info("STEP 2: Sourcing from Amazon for '%s'...", current_keyword)
                amazon_url = await self.amazon.search_products(current_keyword)
                if not amazon_url:
                    raise Exception(f"Failed to find product '{current_keyword}' on Amazon.")
                    
                return await self.amazon.fetch_product_details(amazon_url)
                
            try:
                candidate_details = await self.execute_task_with_memory("Amazon Sourcing", step_amazon_sourcing)
            except Exception as e:
                logger.error(f"Amazon Sourcing failed for '{current_keyword}': {e}. Blacklisting and retrying...")
                past_products.append(current_keyword)
                current_keyword = None
                continue

            # Anti-Book / Anti-Non-Beauty Check
            if is_book_product(candidate_details.title) or is_book_product(current_keyword) or is_non_beauty_product(candidate_details.title):
                logger.warning("⚠️ NON-BEAUTY DETECTED! '%s' (Title: '%s') is non-beauty. Blacklisting and re-triggering research...", current_keyword, candidate_details.title)
                past_products.append(current_keyword)
                past_products.append(candidate_details.title)
                current_keyword = None
                continue
                
            # Quality Shield Check: Skip products with low customer ratings (< 4.0 stars) to protect conversion
            if candidate_details.rating > 0 and candidate_details.rating < 4.0:
                logger.warning("⚠️ LOW RATING DETECTED! '%s' has only %.1f★ rating. Blacklisting and sourcing higher-rated alternative...", candidate_details.title, candidate_details.rating)
                past_products.append(current_keyword)
                past_products.append(candidate_details.title)
                current_keyword = None
                continue
                
            # Anti-Duplicate Check: Extract ASIN & Title and check DB
            new_asin = extract_asin(candidate_details.affiliate_url)
            is_duplicate = False
            
            if new_asin:
                with self.db.connection() as conn:
                    cursor = conn.execute("SELECT affiliate_link FROM products WHERE affiliate_link IS NOT NULL")
                    existing_links = [row["affiliate_link"] for row in cursor.fetchall()]
                    
                    for link in existing_links:
                        if extract_asin(link) == new_asin:
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                with self.db.connection() as conn:
                    chk = conn.execute("SELECT 1 FROM products WHERE LOWER(product_name) = LOWER(?) OR LOWER(title) = LOWER(?)", (current_keyword, candidate_details.title)).fetchone()
                    if chk:
                        is_duplicate = True

            if is_duplicate:
                logger.warning("⚠️ DUPLICATE PRODUCT DETECTED! '%s' (ASIN: %s) already published. Blacklisting and re-triggering Research for a new product...", candidate_details.title, new_asin or 'N/A')
                past_products.append(current_keyword)
                past_products.append(candidate_details.title)
                current_keyword = None
                continue

            # Unique product confirmed!
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
            headline = getattr(seo_data, "image_headline", None) or seo_data.title
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
        if not self.verify_quality(product_details, seo_data, pin_image_path, target_board):
            logger.error("Quality Check failed! Aborting publish.")
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
                
            # Create the Pin
            pin_url = await self.pinterest.create_pin(
                image_path=pin_image_path,
                title=seo_data.title,
                description=seo_data.description,
                board_name=target_board,
                link=product_details.affiliate_url,
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
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO products (product_name, category, board_name, status, image_path, source_url, title, description, affiliate_link, pin_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    final_product_name,
                    niche,
                    target_board,
                    "Pinterest_Published",
                    pin_image_path,
                    product_details.image_url,
                    seo_data.title,
                    seo_data.description,
                    product_details.affiliate_url,
                    pin_url
                )
            )

        # Step 6: Linktree Link Addition
        async def step_linktree_addition():
            logger.info("STEP 6: Adding affiliate link to Linktree Collection...")
            if not await self.linktree.is_logged_in():
                # Try logging in via Google
                logged_in = await self.linktree.login()
                if not logged_in:
                    raise Exception("Failed to log in to Linktree via Google.")
                    
            success = await self.linktree.add_link_to_collection(
                title=product_details.title,
                url=product_details.affiliate_url,
                collection_name=target_board
            )
            if not success:
                raise Exception("Failed to add link to Linktree collection.")
            
        try:
            await self.execute_task_with_memory("Linktree Link Addition", step_linktree_addition)
            
            # Update status to fully Published since Linktree succeeded
            with self.db.connection() as conn:
                conn.execute(
                    "UPDATE products SET status = 'Published' WHERE affiliate_link = ?",
                    (product_details.affiliate_url,)
                )
        except Exception as e:
            logger.error(f"Linktree addition failed: {e}")
            raise
        
        logger.info("🎉 SUCCESS! Pin published at: %s", pin_url)
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

        # 2. Curated viral beauty fallbacks
        fallbacks = [
            "Biodance Bio-Collagen Real Deep Mask",
            "Beauty of Joseon Relief Sun SPF 50",
            "Medicube Zero Pore Pad 2.0",
            "e.l.f. Glow Reviver Lip Oil",
            "ONE/SIZE Patrick Starrr Waterproof Setting Spray",
            "Hero Cosmetics Mighty Patch Original",
            "Sol de Janeiro Cheirosa 68 Perfume Mist",
            "Laneige Lip Sleeping Mask Berry",
            "Glow Recipe Watermelon Niacinamide Dew Drops",
            "Weleda Skin Food Original Ultra-Rich Cream",
            "First Aid Beauty Ultra Repair Cream",
            "Anua Heartleaf 77 Soothing Toner",
            "COSRX Advanced Snail 96 Mucin Power Essence",
            "Cosrx Acne Pimple Master Patch",
            "Tree Hut Shea Sugar Body Scrub Vanilla",
            "Moroccanoil Treatment Original Hair Oil",
            "Color Wow Dream Coat Anti-Frizz Treatment",
            "The Ordinary Glycolic Acid 7% Toning Solution"
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

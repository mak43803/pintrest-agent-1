"""
Trend Database Manager — Isolated DB Layer for Product Intelligence.
=====================================================================
Manages the database/trending_products.db SQLite database.

Strict Business Rules Enforcement:
    1. Daily Fresh Top 5 Selection: Selects ONLY the top 5 highest-scored virals.
    2. Strict Anti-Duplicate History: NEVER selects previously Pinned products.
    3. Clean Active Queue: Keeps ONLY the top 5 fresh active products in the daily queue.
"""

from __future__ import annotations

import sys
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from .trend_models import TrendingProduct, _utc_now

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = Path("database/trending_products.db")


class TrendDatabaseManager:
    """
    Manages SQLite connection and CRUD operations for trending product pool.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize SQLite table for trending product pool."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_product_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    brand TEXT,
                    category TEXT,
                    trend_score INTEGER DEFAULT 0,
                    source_platform TEXT,
                    geo_target TEXT DEFAULT 'US',
                    affiliate_url TEXT,
                    price_usd REAL DEFAULT 0.0,
                    target_board TEXT,
                    dupe_target_brand TEXT,
                    status TEXT DEFAULT 'Queued',
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(product_name, brand)
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trend_score ON trending_product_pool(trend_score DESC);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON trending_product_pool(status);
            """)
            conn.commit()

    def add_product(self, product: TrendingProduct) -> Optional[int]:
        """
        Add a product to the pool if not already present.
        Returns product ID if inserted, None if duplicate.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO trending_product_pool (
                        product_name, brand, category, trend_score,
                        source_platform, geo_target, affiliate_url, price_usd,
                        target_board, dupe_target_brand, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product.product_name,
                    product.brand,
                    product.category,
                    product.trend_score,
                    product.source_platform,
                    product.geo_target,
                    product.affiliate_url,
                    product.price_usd,
                    product.target_board,
                    product.dupe_target_brand,
                    product.status,
                    product.created_at,
                    product.updated_at,
                ))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("""
                    UPDATE trending_product_pool
                    SET trend_score = MAX(trend_score, ?),
                        updated_at = ?
                    WHERE product_name = ? AND brand = ? AND status != 'Pinned'
                """, (product.trend_score, _utc_now(), product.product_name, product.brand))
                conn.commit()
                return None

    def get_fresh_daily_top_5_virals(self) -> List[TrendingProduct]:
        """
        Select ONLY the top 5 highest PIS-scoring unpinned products.
        Strictly excludes any previously Pinned items (Zero Duplicate Guarantee).
        Updates daily active queue status to 'Daily_Top_5_Active'.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Fetch top 5 highest scored items that have NEVER been pinned
            cursor.execute("""
                SELECT * FROM trending_product_pool
                WHERE status NOT IN ('Pinned', 'Skipped')
                ORDER BY trend_score DESC, created_at DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            top5 = [TrendingProduct.from_row(dict(r)) for r in rows]

            # 2. Reset any old active queue items to 'Pool'
            cursor.execute("""
                UPDATE trending_product_pool
                SET status = 'Pool'
                WHERE status = 'Daily_Top_5_Active'
            """)

            # 3. Set newly selected top 5 items to 'Daily_Top_5_Active'
            for p in top5:
                if p.id:
                    cursor.execute("""
                        UPDATE trending_product_pool
                        SET status = 'Daily_Top_5_Active', updated_at = ?
                        WHERE id = ?
                    """, (_utc_now(), p.id))

            conn.commit()
            return top5

    def mark_as_pinned(self, product_id: int) -> bool:
        """
        Mark a product as Pinned.
        Once pinned, it will NEVER be selected again in any future daily top 5!
        """
        return self.update_status(product_id, "Pinned")

    def update_status(self, product_id: int, status: str) -> bool:
        """Update product status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trending_product_pool
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, _utc_now(), product_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Return summary metrics of the product pool."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trending_product_pool")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trending_product_pool WHERE status = 'Daily_Top_5_Active'")
            active_top5 = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trending_product_pool WHERE status = 'Pinned'")
            pinned = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trending_product_pool WHERE trend_score >= 30 AND status != 'Pinned'")
            high_priority = cursor.fetchone()[0]

            return {
                "total_products": total,
                "active_daily_top5": active_top5,
                "pinned_history": pinned,
                "unpinned_high_priority_30plus": high_priority,
            }


if __name__ == "__main__":
    db = TrendDatabaseManager()
    print("✅ TrendDatabaseManager initialized with Strict Top 5 + Anti-Duplicate rules.")
    top5 = db.get_fresh_daily_top_5_virals()
    print(f"🔥 Fresh Daily Top 5 Virals (Strictly Unpinned): {len(top5)} items")
    for idx, p in enumerate(top5, start=1):
        print(f"   {idx}. [{p.geo_target} | {p.source_platform}] {p.brand} - {p.product_name} | PIS: {p.trend_score}/40 | Status: {p.status}")

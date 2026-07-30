"""
View Pending / Queued Products in Agent Database
"""
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db_path = Path("database/pinterest_ai_agent.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, product_name, category, source_url, created_at FROM products WHERE status = 'Pending_Pin' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(f" 📦 AGENT QUEUE AUDIT — TOTAL QUEUED PRODUCTS: {len(rows)}")
    print("═════════════════════════════════════════════════════════════════")

    # Category breakdown
    cat_counts = {}
    for r in rows:
        cat = r[2] or "Uncategorized"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print("📊 CATEGORY BREAKDOWN:")
    for cat, count in cat_counts.items():
        print(f"   • {cat}: {count} products")

    print(f"\n--- SAMPLE RECENTLY QUEUED PRODUCTS (FIRST 25 OF {len(rows)}) ---")
    for idx, r in enumerate(rows[:25], start=1):
        print(f" [{idx:02d}] ID #{r[0]}: {r[1][:55]} | Cat: {r[2]}")

if __name__ == "__main__":
    main()

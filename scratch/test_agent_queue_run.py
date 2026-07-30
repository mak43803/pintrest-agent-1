"""
Test Pinterest Agent Pre-Seeded Queue Instantiation
"""
import sys
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(".").resolve()))
from browser.amazon_client import AmazonProduct

def main():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.execute("SELECT id, product_name, category, board_name, title, image_path, affiliate_link FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()

    if row:
        prod = AmazonProduct(
            title=row[4] or row[1],
            description=f"Discover {row[4]}. Viral Sephora Find!",
            price="$16.99",
            rating=4.8,
            review_count=15000,
            image_url=row[5] or "",
            affiliate_url=row[6] or ""
        )
        print("✅ AmazonProduct Instantiated Successfully:")
        print(f"   • Title: {prod.title}")
        print(f"   • Image: {prod.image_url}")
        print(f"   • Link:  {prod.affiliate_url}")
    else:
        print("No pending rows.")
    conn.close()

if __name__ == "__main__":
    main()

"""
Inspect Latest Published Pin in Database
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

    cursor.execute("""
        SELECT id, product_name, category, board_name, status, source_url, 
               title, description, affiliate_link, image_path, pin_url, created_at 
        FROM products WHERE status = 'Pinterest_Published' AND pin_url IS NOT NULL ORDER BY id DESC LIMIT 3
    """)
    rows = cursor.fetchall()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(" 📌 LATEST PUBLISHED PINS IN DATABASE")
    print("═════════════════════════════════════════════════════════════════")

    for idx, r in enumerate(rows, start=1):
        print(f"\n[{idx}] PUBLISHED PIN ID #{r[0]}")
        print(f"    • Product Name  : {r[1]}")
        print(f"    • Category      : {r[2]}")
        print(f"    • Board Name    : {r[3]}")
        print(f"    • Pin URL       : {r[10]}")
        print(f"    • Image Path    : {r[9]}")
        print(f"    • Affiliate Link: {r[8]}")

if __name__ == "__main__":
    main()

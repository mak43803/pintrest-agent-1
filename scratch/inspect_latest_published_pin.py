import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, product_name, title, category, board_name, affiliate_link, pin_url, status, updated_at FROM products WHERE status = 'Pinterest_Published' ORDER BY updated_at DESC, id DESC LIMIT 5").fetchall()

print("LAST 5 PUBLISHED PINS IN DB:")
print("=" * 110)
for r in rows:
    print(f"ID #{r['id']} | Category: {r['category']}")
    print(f"  Product Name   : {r['product_name']}")
    print(f"  SEO Title      : {r['title']}")
    print(f"  Board          : {r['board_name']}")
    print(f"  Affiliate Link : {r['affiliate_link']}")
    print(f"  Pin URL        : {r['pin_url']}")
    print(f"  Updated At     : {r['updated_at']}")
    print("-" * 110)

conn.close()

import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, product_name, title, affiliate_link, pin_url, status FROM products ORDER BY id DESC LIMIT 15").fetchall()

print(f"{'ID':<6} | {'Status':<18} | {'Product Name':<30} | {'Affiliate Link'}")
print("-" * 100)
for r in rows:
    pname = (r['product_name'] or r['title'] or '')[:30]
    aff = r['affiliate_link'] or ''
    print(f"{r['id']:<6} | {r['status']:<18} | {pname:<30} | {aff}")

conn.close()

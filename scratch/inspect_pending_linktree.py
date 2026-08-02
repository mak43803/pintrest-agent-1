import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, product_name, category, board_name, affiliate_link, pin_url FROM products WHERE status = 'Pinterest_Published'")
rows = cursor.fetchall()

print(f"Found {len(rows)} products pending Linktree sync:\n")
for r in rows:
    print(f"ID        : {r[0]}")
    print(f"Product   : {r[1]}")
    print(f"Board     : {r[3]}")
    print(f"Affiliate : {r[4]}")
    print(f"Pin URL   : {r[5]}")
    print("-" * 60)

conn.close()

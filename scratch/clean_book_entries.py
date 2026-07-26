import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.pinterest_agent import is_book_product

conn = sqlite3.connect('database/pinterest_ai_agent.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, product_name, category, board_name, title, affiliate_link FROM products").fetchall()

print(f"Total products in DB before cleanup: {len(rows)}")

deleted_ids = []
for r in rows:
    d = dict(r)
    full_text = f"{d['product_name']} {d['category']} {d['board_name']} {d['title']} {d['affiliate_link']}"
    if is_book_product(full_text):
        deleted_ids.append(d['id'])
        print(f"Deleting Book Entry ID {d['id']}: Product='{d['product_name']}' | Title='{d['title']}'")

if deleted_ids:
    placeholders = ",".join("?" * len(deleted_ids))
    conn.execute(f"DELETE FROM products WHERE id IN ({placeholders})", deleted_ids)
    conn.commit()
    print(f"\nSuccessfully cleaned up {len(deleted_ids)} book entries from database.")
else:
    print("No book entries found in database.")

remaining = conn.execute("SELECT COUNT(*) as cnt FROM products").fetchone()["cnt"]
print(f"Total products remaining in DB: {remaining}")
conn.close()

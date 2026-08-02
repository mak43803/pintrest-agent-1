import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.execute("SELECT id, product_name, status, pin_url FROM products WHERE pin_url LIKE '%pin-builder%'")
rows = cursor.fetchall()
print(f"Found {len(rows)} fake published pins with pin-builder URL:")
for r in rows:
    print(f"  ID #{r['id']}: {r['product_name']} | URL: {r['pin_url']}")

conn.execute("UPDATE products SET status = 'Queued', pin_url = NULL WHERE pin_url LIKE '%pin-builder%'")
conn.commit()
print("SUCCESS: Reset fake pin-builder products back to Queued state!")
conn.close()

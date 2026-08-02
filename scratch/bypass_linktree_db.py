import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update all Pinterest_Published products directly to Published
cursor.execute("UPDATE products SET status = 'Published' WHERE status = 'Pinterest_Published'")
updated_count = cursor.rowcount
conn.commit()

print(f"Updated {updated_count} products from 'Pinterest_Published' to 'Published'.")

# Print current status breakdown
cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
rows = cursor.fetchall()
print("\n=== UPDATED PRODUCT STATUS BREAKDOWN ===")
for st, cnt in rows:
    print(f"  • {st}: {cnt}")

conn.close()

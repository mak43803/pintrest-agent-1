import sqlite3

conn = sqlite3.connect('database/pinterest_ai_agent.db')
cursor = conn.cursor()

cursor.execute("SELECT status, count(*) FROM products GROUP BY status")
print("Status Counts:", dict(cursor.fetchall()))

cursor.execute("SELECT id, product_name, status, created_at FROM products WHERE status='Pending_Pin' ORDER BY id ASC LIMIT 5")
print("\nFirst 5 Pending_Pin items:")
for r in cursor.fetchall():
    print(r)

cursor.execute("SELECT id, product_name, status, created_at FROM products WHERE status='Pending_Pin' ORDER BY id DESC LIMIT 5")
print("\nLast 5 Pending_Pin items:")
for r in cursor.fetchall():
    print(r)

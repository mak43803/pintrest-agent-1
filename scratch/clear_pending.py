import sqlite3

db_path = r"database/pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)

cursor = conn.cursor()
cursor.execute("UPDATE products SET status = 'Published' WHERE status = 'Pinterest_Published'")
updated_count = cursor.rowcount
conn.commit()
conn.close()

print(f"Updated {updated_count} pending products to Published.")

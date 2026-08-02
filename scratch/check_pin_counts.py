import sqlite3

conn = sqlite3.connect('database/pinterest_ai_agent.db')
cursor = conn.cursor()

cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
status_counts = dict(cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'Published'")
total_published = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products")
total_products = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'Published' AND date(updated_at) = date('now')")
today_published = cursor.fetchone()[0]

cursor.execute("SELECT updated_at FROM products WHERE status = 'Published' ORDER BY id DESC LIMIT 1")
last_published_time = cursor.fetchone()
last_time = last_published_time[0] if last_published_time else "None"

print("--- PINTEREST AGENT DATABASE STATS ---")
print(f"Total Products in DB: {total_products}")
print(f"Total Pins Published: {total_published}")
print(f"Today Published Pins: {today_published}")
print(f"Last Pin Published At: {last_time}")
print("\nStatus Breakdown:")
for k, v in status_counts.items():
    print(f"  - {k}: {v}")

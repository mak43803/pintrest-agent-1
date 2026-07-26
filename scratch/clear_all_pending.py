import os, sqlite3

db_files = [
    r"database/pinterest_ai_agent.db",
    r"pinterest_ai_agent.db",
    r"database/pinterest_agent.db",
    r"pinterest_agent.db"
]

total_updated = 0
for f in db_files:
    if os.path.exists(f):
        try:
            conn = sqlite3.connect(f)
            cursor = conn.cursor()
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if 'products' in tables:
                cursor.execute("UPDATE products SET status = 'Published' WHERE status = 'Pinterest_Published'")
                cnt = cursor.rowcount
                conn.commit()
                print(f"File {f}: Updated {cnt} pending products to Published.")
                total_updated += cnt
            conn.close()
        except Exception as e:
            print(f"Error on {f}: {e}")

print(f"Total pending products updated across all DB files: {total_updated}")

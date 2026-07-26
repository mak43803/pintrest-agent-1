import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

print(f"Connecting to database at: {db_path.resolve()}")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== Checking for products with status != 'Published' ===")
cursor.execute("SELECT id, product_name, category, status, created_at, affiliate_link FROM products WHERE status != 'Published'")
rows = cursor.fetchall()
if not rows:
    print("No products with status != 'Published' found.")
else:
    for row in rows:
        print(f"ID: {row['id']} | Product: {row['product_name']} | Category: {row['category']} | Status: {row['status']} | Date: {row['created_at']}")
        print(f"  Link: {row['affiliate_link']}")

print("\n=== Checking last 10 failed tasks in tasks table ===")
try:
    cursor.execute("SELECT id, task_name, current_step, status, last_error, finished_at FROM tasks WHERE status = 'Failed' OR last_error IS NOT NULL ORDER BY id DESC LIMIT 10")
    tasks = cursor.fetchall()
    if not tasks:
        print("No failed tasks found.")
    else:
        for t in tasks:
            print(f"Task ID: {t['id']} | Name: {t['task_name']} | Step: {t['current_step']} | Status: {t['status']} | Finished: {t['finished_at']}")
            print(f"  Last Error: {t['last_error']}")
except Exception as e:
    print(f"Error querying tasks: {e}")

print("\n=== Checking last 10 ERROR logs in logs table ===")
try:
    cursor.execute("SELECT id, level, message, module, created_at FROM logs WHERE level = 'ERROR' ORDER BY id DESC LIMIT 10")
    logs = cursor.fetchall()
    if not logs:
        print("No ERROR logs found.")
    else:
        for l in logs:
            print(f"Log ID: {l['id']} | Level: {l['level']} | Module: {l['module']} | Date: {l['created_at']}")
            print(f"  Message: {l['message']}")
except Exception as e:
    print(f"Error querying logs: {e}")

conn.close()

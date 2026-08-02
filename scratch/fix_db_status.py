import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET status = 'Published' WHERE status = 'Pinterest_Published'")
    conn.commit()
    print(f"Successfully updated {cursor.rowcount} products to status 'Published' (Linktree bypassed).")
    conn.close()

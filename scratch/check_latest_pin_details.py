import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM products WHERE status = 'Pinterest_Published' ORDER BY updated_at DESC, id DESC LIMIT 3").fetchall()

for r in rows:
    print(f"ID #{r['id']}:")
    for key in r.keys():
        val_str = str(r[key]).encode("ascii", errors="replace").decode("ascii")
        print(f"  {key:<15}: {val_str}")
    print("=" * 80)

conn.close()

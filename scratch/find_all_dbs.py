import os, sqlite3

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".db"):
            full_path = os.path.join(root, file)
            try:
                conn = sqlite3.connect(full_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                if 'products' in tables:
                    total = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                    statuses = cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status").fetchall()
                    print(f"DB Path: {full_path} | Total Products: {total}")
                    for s in statuses:
                        print(f"   - {s[0]}: {s[1]}")
                conn.close()
            except Exception as e:
                print(f"Could not read {full_path}: {e}")

import sqlite3
import os

db_paths = ["database/pinterest_ai_agent.db", "database/trending_products.db", "pinterest_ai_agent.db"]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"\n--- Checking {db_path} ---")
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check tables
            tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            print("Tables:", tables)
            
            if "products" in tables:
                # Count by status
                stats = cursor.execute("SELECT status, COUNT(*) as cnt FROM products GROUP BY status").fetchall()
                print("Status counts:")
                for r in stats:
                    print(f"  {r['status']}: {r['cnt']}")
                
                # Check pending or processing with bad affiliate link
                bad_rows = cursor.execute("""
                    SELECT id, product_name, affiliate_link, source_url, status 
                    FROM products 
                    WHERE status IN ('Pending_Pin', 'Processing') 
                    AND (affiliate_link IS NULL OR affiliate_link = '' OR affiliate_link NOT LIKE 'http%')
                """).fetchall()
                
                print(f"Bad pending/processing rows count: {len(bad_rows)}")
                for b in bad_rows[:10]:
                    print(f"  ID #{b['id']}: name='{b['product_name']}', aff='{b['affiliate_link']}', src='{b['source_url']}', status='{b['status']}'")
            conn.close()
        except Exception as e:
            print(f"Error checking {db_path}: {e}")

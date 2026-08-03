import sys
sys.path.insert(0, ".")
import sqlite3

def check():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, product_name, status, created_at FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 20")
    rows = cursor.fetchall()
    print(f"--- Top 20 Pending Products in DB Queue (Total: {len(rows)}) ---")
    for r in rows:
        print(f" ID #{r[0]} | Title: {r[1]} | Name: {r[2]} | Status: {r[3]}")
        
    conn.close()

if __name__ == "__main__":
    check()

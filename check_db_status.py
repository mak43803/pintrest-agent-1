import sqlite3

def main():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.cursor()
    
    # 1. Total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    
    # 2. Count by status
    cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
    statuses = cursor.fetchall()
    
    print("DATABASE SUMMARY:")
    print(f"Total Products in DB: {total}")
    print("\nStatus Breakdown:")
    for status, count in statuses:
        print(f"  - {status}: {count}")
        
    # 3. Recent 10 products
    cursor.execute("SELECT id, title, status, created_at FROM products ORDER BY id DESC LIMIT 10")
    recents = cursor.fetchall()
    
    print("\nRecent 10 Products:")
    for r in recents:
        print(f"  [#{r[0]}] Status: {r[2]} | Title: '{(r[1] or '')[:60]}'")
        
    conn.close()

if __name__ == "__main__":
    main()

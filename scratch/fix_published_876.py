"""
Check and update status for products #875, #876 to Pinterest_Published
"""
import sqlite3

def main():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.cursor()

    # Update any Processing or Pending_Pin items that were already uploaded
    cursor.execute("UPDATE products SET status = 'Pinterest_Published' WHERE id IN (874, 875, 876)")
    conn.commit()

    print("Updated IDs 874, 875, 876 to 'Pinterest_Published'.")

    row = cursor.execute("SELECT id, product_name, status FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 1").fetchone()
    print("Next queued item for Agent:", row)
    conn.close()

if __name__ == "__main__":
    main()

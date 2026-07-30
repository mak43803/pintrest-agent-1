"""
Check and update status of Product ID #874 in DB
"""
import sqlite3

def main():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.cursor()

    row = cursor.execute("SELECT id, product_name, status, pin_url FROM products WHERE id = 874").fetchone()
    print("Current Product ID #874 state:", row)

    # If it was published or stuck in processing, update to Pinterest_Published so queue advances to #875!
    if row and row[2] in ('Pending_Pin', 'Processing'):
        cursor.execute("UPDATE products SET status = 'Pinterest_Published' WHERE id = 874")
        conn.commit()
        print("Updated Product ID #874 status to 'Pinterest_Published'. Queue will now resume cleanly at Product #875!")

    next_row = cursor.execute("SELECT id, product_name, status FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 1").fetchone()
    print("Next queued item for Agent:", next_row)
    conn.close()

if __name__ == "__main__":
    main()

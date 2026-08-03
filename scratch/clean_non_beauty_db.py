import sys
sys.path.insert(0, ".")
import sqlite3

def clean_db():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    cursor = conn.cursor()
    
    non_beauty_terms = [
        "%toy%", "%mystery capsule%", "%zuru%", "%hoodie%", "%lounge%", "%cup%", "%tumbler%",
        "%decor%", "%curtain%", "%pillow%", "%chair%", "%book%", "%kindle%", "%handbook%", "%paperback%"
    ]
    
    deleted_total = 0
    for term in non_beauty_terms:
        cursor.execute("DELETE FROM products WHERE (title LIKE ? OR product_name LIKE ?) AND status = 'Pending_Pin'", (term, term))
        deleted_total += cursor.rowcount
        
    conn.commit()
    print(f"Purged {deleted_total} non-beauty pending products from database.")
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'Pending_Pin'")
    remaining = cursor.fetchone()[0]
    print(f"Remaining pending products in queue: {remaining}")
    conn.close()

if __name__ == "__main__":
    clean_db()

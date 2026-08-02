import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
conn = sqlite3.connect(db_path)

conn.execute("""
    UPDATE products 
    SET product_name = 'Clinique Moisture Surge 72-Hour Auto-Replenishing Hydrator',
        title = 'Clinique Moisture Surge 72-Hour Auto-Replenishing Hydrator',
        description = 'Looking for the best Clinique Moisture Surge 72-Hour Auto-Replenishing Hydrator for your everyday beauty routine in the US, UK, and Canada? This high-performance formula is the ultimate Sephora & Amazon beauty find! Click the link to check live price & read 15,000+ verified 5-star customer reviews on Amazon. 💾 Save this pin! #AmazonBeautyFinds #SephoraDupes #CleanGirlAesthetic'
    WHERE id = 995
""")
conn.commit()
conn.close()
print("Product 995 successfully updated!")

import sys

file_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\gemini_web_client.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find('    async def generate_product_idea(')
if start_idx == -1:
    print("Could not find generate_product_idea")
    sys.exit(1)

new_method = '''    async def generate_product_idea(self, niche: str = "latest beauty products", past_products: list[str] = None, live_trends: str = "", google_trends: str = "", amazon_best_sellers: str = "") -> str:
        """
        Ask Gemini for a highly specific, trending product keyword using live Pinterest trends.
        """
        past_str = ""
        if past_products:
            past_str = "\\nDO NOT suggest any of these products, as I have already posted them:\\n" + "\\n".join(f"- {p}" for p in past_products)

        trends_str = ""
        if live_trends:
            trends_str = f"\\nLIVE PINTEREST TRENDS TODAY:\\n{live_trends}\\n(Use these to inspire your beauty product choice if relevant!)\\n"

        prompt = f"""
###############################################################
PINTEREST SHOPPING TRENDS NAVIGATION
###############################################################

This is the FIRST task.
Do not guess.
Do not search manually.
Follow these steps exactly.

---------------------------------------------------------------
STEP 1
---------------------------------------------------------------
Open: https://trends.pinterest.com
Wait until the website is fully loaded.

---------------------------------------------------------------
STEP 2
---------------------------------------------------------------
Look at the LEFT SIDEBAR.
You will see three options.
1. Trend Overview
2. Shopping Trends
3. Search Trends

Click ONLY: Shopping Trends
Wait until the Shopping Trends page is fully loaded.

---------------------------------------------------------------
STEP 3
---------------------------------------------------------------
Verify the Region.
If Region is not: United States
Change it to: United States
Wait until the page refreshes completely.

---------------------------------------------------------------
STEP 4
---------------------------------------------------------------
At the top of the page you will see two tabs.
• Trending Categories
• All Categories

Click: All Categories
Wait until all categories load.

---------------------------------------------------------------
STEP 5
---------------------------------------------------------------
After clicking All Categories,
Look for the category tile named: Beauty

Click: Beauty
Wait until all Beauty product categories appear.

---------------------------------------------------------------
STEP 6
---------------------------------------------------------------
You are now inside the Beauty section.
You will see many Beauty categories such as:
Bath & Body, Body Care, Body Moisturizers, Body Washes, Beauty Supplements
Blushes & Bronzzers, Brow Makeup, Eye Makeup, Eyeliners, Eyeshadow, Face Makeup, Facial Cleansers
Face Lotions & Creams, Hair Care, Hair Shampoo, Hair Conditioner, Hair Oil, Hair Serum, Hair Mask
Hair Growth, Lip Care, Lip Gloss, Lip Oil, Lipstick, Moisturizers, Serums & Essences, Skincare
Skincare Masks & Peels, Sunscreen, Teeth Whitening, Toners & Astringents
and many more.

---------------------------------------------------------------
STEP 7
---------------------------------------------------------------
Open the FIRST Beauty category.
Example: Bath & Body
Wait until the category page loads.

---------------------------------------------------------------
STEP 8
---------------------------------------------------------------
Scroll down.
Find the section: Top Products On Pinterest

If needed, click: Explore Top Products
Wait for the popup or product list.

---------------------------------------------------------------
STEP 9
---------------------------------------------------------------
Read every product name.
Merchant does NOT matter.
Amazon, Target, Sephora, Ulta, Walmart, CVS, Native, SHEIN
Any merchant is acceptable.

Your goal is ONLY to find ONE trending beauty product.

---------------------------------------------------------------
STEP 10
---------------------------------------------------------------
Copy ONLY the Product Name.
Do not choose more than one product.
After selecting one product, stop Pinterest research and continue to the Amazon workflow.

---------------------------------------------------------------
IMPORTANT
---------------------------------------------------------------
Never skip steps.
Always wait 2–3 seconds after every click.
Always wait until the page is completely loaded.
Never rush.
Never use Search.
Always navigate using:
Shopping Trends
↓
All Categories
↓
Beauty
↓
Beauty Category
↓
Top Products
↓
Choose One Product
↓
Continue to Amazon.

{trends_str}

{past_str}

Return only ONE final product per research cycle. Give me EXACTLY ONE highly specific, trending product search term that I should type into Amazon.
Do not give me a list. Do not use quotes. Just the raw search term.
Example: COSRX Snail Mucin 96% Power Repairing Essence
"""
        response = await self._send_prompt(prompt)
        
        if response:
            return response.strip().replace('"', "")
        return niche
'''

new_content = content[:start_idx] + new_method

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Restored gemini_web_client.py with the NEW Shopping Trends prompt!")

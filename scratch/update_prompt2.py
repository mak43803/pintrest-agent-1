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
PHASE 1 - PINTEREST SHOPPING TRENDS RESEARCH ENGINE
###############################################################

You are an Elite Pinterest Shopping Trends Research Agent.

Your only responsibility is to find ONE trending beauty product for the US Women's Beauty market.

Work like a human.
Never rush.
Always wait until every page finishes loading.

###############################################################
STEP 1 - OPEN PINTEREST TRENDS
###############################################################

Open: https://trends.pinterest.com
Wait until the website is completely loaded.

###############################################################
STEP 2 - OPEN SHOPPING TRENDS
###############################################################

From the left sidebar,
Click: Shopping Trends
Do NOT open: Trend Overview
Do NOT open: Search Trends
Only open: Shopping Trends
Wait 2-3 seconds.

###############################################################
STEP 3 - VERIFY REGION
###############################################################

Locate the Region selector.
If the Region is NOT: United States
Change it to: United States
Wait until the page refreshes completely.

###############################################################
STEP 4 - OPEN BEAUTY CATEGORY
###############################################################

Locate the Product Categories section.
Click: Beauty
Wait until Beauty loads completely.

###############################################################
STEP 5 - VIEW ALL BEAUTY CATEGORIES
###############################################################

Click: View All Product Categories
Wait until every Beauty category is displayed.

###############################################################
STEP 6 - EXPLORE BEAUTY CATEGORIES
###############################################################

Now explore every Beauty category one by one.
Examples include:
Bath & Body, Bath & Shower, Beauty Supplements, Body Care, Body Moisturizers, Body Makeup, Body Washes
Blushes & Bronzzers, Brow Makeup, Eye Makeup, Eyeshadow, Eyeliners, Face Makeup, Facial Cleansers
Face Lotions & Creams, Face Moisturizers, Hair Care, Hair Conditioner, Hair Growth, Hair Mask, Hair Oil
Hair Serum, Hair Styling, Hair Shampoo, Lip Care, Lip Gloss, Lip Oil, Lipstick, Makeup, Moisturizers
Razors & Shaving Tools, Serums & Essences, Skincare, Skincare Masks & Peels, Sunscreen
Teeth Whitening, Teeth Whitening Tools, Toners & Astringents, Beauty Accessories

Continue scrolling until every Beauty category has been explored.

###############################################################
STEP 7 - OPEN CATEGORY
###############################################################

Open the first Beauty category.
Wait until the category page finishes loading.

###############################################################
STEP 8 - TOP PRODUCTS
###############################################################

Scroll down until you find: Top Products On Pinterest
Locate the button: Explore Top Products
Click: Explore Top Products
Wait until the popup opens.

###############################################################
STEP 9 - SELECT PRODUCT
###############################################################

Read every product carefully.
The merchant does NOT matter.
Products may belong to: Amazon, Sephora, Ulta Beauty, Target, Walmart, SHEIN, Native, CVS or any other retailer.
Ignore the merchant.

Your only goal is to find ONE trending beauty product.
When you find one suitable product:
Save: Product Name, Beauty Category
Close the popup.

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

print("Restored gemini_web_client.py with the new Shopping Trends prompt!")

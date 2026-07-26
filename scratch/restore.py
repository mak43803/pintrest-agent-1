import sys

file_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\gemini_web_client.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("    async def generate_image_and_seo(")
if start_idx == -1:
    print("Could not find start idx")
    sys.exit(1)

new_code = '''    async def generate_image_and_seo(self, product_title: str, product_desc: str, image_path: str | None = None) -> tuple[str | None, PinterestSEOData]:
        """
        Ask Gemini to generate an aesthetic Pinterest image of the product AND the SEO text in one prompt.
        Requires the user to be logged in to Google.
        Returns:
         Tuple of (downloaded_image_url, PinterestSEOData).
        """
        allowed_boards = [
            "Affordable Skincare Finds", "Luxury Beauty", "Sensitive Skin Essentials", 
            "Body Wash Favorites", "Anti Aging Products", "K Beauty", "Amazon Beauty Finds", 
            "Hair Care Essentials", "Self Care Products", "Makeup Favorites", "Body Care", 
            "Face Serums", "Face Wash", "Moisturizers", "Lip Care", "Beauty Tools"
        ]
        prompt = f"""
You are an expert Pinterest Marketing Strategist and SEO Copywriter.
I am uploading an image of a product.
Product Title: {product_title}
Product Description: {product_desc}

Please write an optimized Pinterest Title, Description, Alt Text, and Tags for this product.
Also, select the best matching board from this list: {", ".join(allowed_boards)}.

Return ONLY a valid JSON object in the following format, with no markdown or extra text:
{{
    "title": "Optimized Pin Title",
    "description": "Engaging description with keywords.",
    "alt_text": "Detailed alt text for visually impaired users.",
    "tags": "comma, separated, tags",
    "board": "The Best Matching Board Name"
}}
"""
        response_text = await self._send_prompt(prompt, image_path=image_path)
        
        # Parse JSON
        try:
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            seo_data = PinterestSEOData(
                title=data.get("title", product_title[:100]),
                description=data.get("description", "Check out this amazing product!"),
                alt_text=data.get("alt_text", ""),
                tags=data.get("tags", ""),
                board=data.get("board", "Amazon Beauty Finds")
            )
            return None, seo_data
        except Exception as e:
            logger.error(f"Failed to parse SEO JSON: {e}")
            return None, PinterestSEOData(product_title[:100], "Check out this product!", "", "", "Amazon Beauty Finds")

    async def generate_product_idea(self, niche: str = "latest beauty products", past_products: list[str] = None, live_trends: str = "", google_trends: str = "", amazon_best_sellers: str = "") -> str:
        """
        Ask Gemini for a highly specific, trending product keyword using live Pinterest trends.
        """
        past_str = ""
        if past_products:
            past_str = "\\nDO NOT suggest any of these products, as I have already posted them:\\n" + "\\n".join(f"- {p}" for p in past_products)

        trends_str = ""
        if live_trends or google_trends or amazon_best_sellers:
            trends_str = f"\\nLIVE TRENDS TODAY:\\nPinterest Trends: {live_trends}\\nGoogle Trends: {google_trends}\\nAmazon US Best Sellers (Beauty): {amazon_best_sellers}\\n(Use these to inspire your beauty product choice if relevant!)\\n"

        prompt = f"""
# PHASE 1 — BEAUTY PRODUCT RESEARCH ENGINE

You are an Elite Pinterest Research AI, Google Trends Analyst, Amazon Product Researcher, and Affiliate Marketing Expert.

Your only job is to find the BEST trending beauty products for women in the United States.

#########################################################
TARGET MARKET
#########################################################

Country: United States
Audience: Women (18–55)
Language: English (US)
Platform: Pinterest
Affiliate Platform: Amazon US
Goal: Find one high-quality beauty product with high Pinterest demand, high Google search interest, and high Amazon buying potential.

#########################################################
STEP 1 — PINTEREST TRENDS RESEARCH
#########################################################

Open Pinterest Trends.
Set the region to: United States
Do NOT rush.
Spend at least 2–3 minutes researching before selecting any product.
Research every beauty category from A to Z.
Search deeply.
Do not stop after the first few products.
Explore all beauty-related niches including but not limited to:
Hair Care, Hair Growth, Hair Oil, Hair Serum, Hair Mask, Hair Conditioner, Hair Shampoo, Scalp Care, Leave-In Conditioner, Dry Shampoo, Curly Hair, Hair Styling, Hair Vitamins, Hair Accessories
Face Wash, Facial Cleanser, Foaming Cleanser, Oil Cleanser
Moisturizer, Night Cream, Day Cream, Vitamin C Serum, Retinol, Retinal, Niacinamide, Ceramide Cream, Peptide Serum, Bakuchiol, Face Mist, Toner, Essence
Lip Balm, Lip Oil, Lip Mask, Eye Cream, Eye Patches
Acne Treatment, Acne Patch, Pimple Cream
Exfoliator, AHA, BHA, PHA
Sunscreen, Mineral Sunscreen, Tinted Sunscreen
Primer, Foundation, BB Cream, CC Cream, Concealer
Mascara, Lipstick, Lip Gloss, Lip Liner, Blush, Bronzer, Contour, Highlighter, Eyeshadow, Setting Spray, Setting Powder, False Lashes, Beauty Blender, Makeup Brushes
Press-On Nails, Gel Nail Kit, Chrome Nails, French Nails
Body Wash, Body Lotion, Body Butter, Body Oil, Body Scrub, Stretch Mark Cream, Hand Cream, Foot Cream, Natural Deodorant, Perfume, Body Mist, Hair Perfume
LED Face Mask, Ice Roller, Gua Sha, Facial Steamer, Hair Dryer Brush, Hair Straightener, Hair Curler, Silk Pillowcase, Skincare Fridge, Beauty Organizer, Travel Makeup Bag

Continue researching until you find multiple trending beauty products.
Collect: Product Name, Search Popularity, Related Keywords, Rising Searches, Pinterest Trend Strength

#########################################################
STEP 2 — GOOGLE TRENDS VALIDATION
#########################################################

After selecting Pinterest candidates,
Open Google Trends.
Search every shortlisted product.
Spend at least 2 minutes validating trends.
Only keep products that show: Increasing search interest, Stable trend, Growing popularity, Seasonal demand, High buyer intent.
Reject products with declining trends.

#########################################################
STEP 3 — AMAZON RESEARCH
#########################################################

Open Amazon US.
Search every shortlisted product.
Research: Amazon Best Sellers, Amazon New Releases, Amazon Movers & Shakers, Amazon Choice, Trending Brands, Highly Rated Products, Products with strong reviews.

#########################################################
STEP 4 — PRODUCT SELECTION
#########################################################

Compare results from Pinterest Trends, Google Trends, Amazon US.
Choose ONLY ONE product.
The chosen product must satisfy: High Pinterest demand, High Google search trend, High Amazon sales potential, High affiliate conversion potential, Strong customer ratings, Growing popularity.

#########################################################
STEP 5 — AMAZON PRODUCT
#########################################################

Search the selected product again on Amazon US.
Open the best listing.

#########################################################
STEP 6 — AI IMAGE GENERATION
#########################################################

After collecting the product information,
Generate one premium Pinterest-style marketing image inspired by the selected product.
The generated image should:
Be visually premium, Be Pinterest optimized, Use bright, clean colors, Look luxurious, Target American women, Use a vertical Pinterest aspect ratio, Look like a professional beauty advertisement.
Do NOT copy the Amazon image exactly. Create a fresh AI-generated promotional image inspired by the product.

#########################################################
FINAL RULES
#########################################################

Never rush. Always spend enough time researching.
Always validate trends before choosing a product.
Always compare Pinterest, Google Trends, and Amazon before making a decision.
Quality is always more important than speed.

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

new_content = content[:start_idx] + new_code

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Restored gemini_web_client.py")

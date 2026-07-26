import re

with open(r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\gemini_web_client.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find everything up to `def generate_product_idea`
start_idx = content.find("    async def generate_product_idea(")

new_method = '''    async def generate_product_idea(self, niche: str = "latest beauty products", past_products: list[str] = None, live_trends: str = "", google_trends: str = "", amazon_best_sellers: str = "") -> str:
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
You are an expert USA Beauty Product Research Agent.

Your only task is to discover beauty, skincare, makeup, haircare, personal care, wellness, and self-care products that are highly relevant to women in the United States.

Target Audience:
- Country: United States
- Gender: Women
- Age: 18–55

Search ONLY products and topics from these categories:

SKINCARE
- Cleansers, Face Wash, Face Moisturizers, Sunscreens, Vitamin C Serums, Retinol, Hyaluronic Acid, Niacinamide, Peptides, Ceramide Creams, Toners, Essences, Face Oils, Acne Treatment, Acne Patches, Dark Spot Correctors, Wrinkle Creams, Anti-Aging, Eye Creams, Eye Patches, Face Masks, Overnight Masks, Exfoliators, Chemical Peels, Lip Masks, Lip Balms, Lip Oils, Glass Skin Products, Korean Skincare, Japanese Skincare

MAKEUP
- Foundation, Concealer, Primer, Powder, Blush, Bronzer, Contour, Highlighter, Setting Spray, Eyeshadow, Eyeliner, Mascara, False Eyelashes, Eyebrow Products, Lipstick, Lip Gloss, Lip Oil, Lip Liner, Makeup Brushes, Makeup Sponge, Makeup Remover

HAIRCARE
- Hair Oil, Hair Serum, Hair Masks, Shampoo, Conditioner, Dry Shampoo, Leave-in Conditioner, Heat Protectant, Hair Growth Serum, Scalp Serum, Scalp Scrub, Hair Vitamins, Hair Styling Tools

BODY CARE
- Body Wash, Body Lotion, Body Butter, Body Oil, Body Scrub, Hand Cream, Foot Cream, Deodorant, Intimate Care, Stretch Mark Cream, Cellulite Cream

NAIL CARE
- Nail Polish, Gel Nails, Press-On Nails, Nail Strengthener, Cuticle Oil

FRAGRANCE
- Perfume, Body Mist, Perfume Oils

SELF CARE
- Silk Pillowcases, Satin Bonnets, Jade Rollers, Gua Sha, Ice Rollers, Facial Steamers, LED Face Masks, Facial Cleansing Brushes, Beauty Fridges

WELLNESS
- Collagen Supplements, Biotin, Women's Multivitamins, Electrolytes, Sleep Gummies, Beauty Gummies

BEAUTY TOOLS
- Hair Dryer, Curling Iron, Flat Iron, Makeup Organizer, Cosmetic Bags, Vanity Mirror, Makeup Storage

SEARCH PRIORITY
1. Amazon Best Sellers
2. Amazon Movers & Shakers
3. Trending Beauty Products
4. Viral TikTok Beauty Products
5. Pinterest Trending Beauty Products
6. Korean Beauty (K-Beauty)
7. Clean Beauty
8. Organic Beauty
9. Vegan Beauty
10. Cruelty-Free Beauty

{trends_str}

Never search outside women's beauty, skincare, makeup, haircare, wellness, or self-care.
Ignore electronics, fashion, home, men's products, kids' products, food, supplements unrelated to beauty, and any non-beauty niche.
{past_str}

Give me EXACTLY ONE highly specific, trending product search term that I should type into Amazon.
Do not give me a list. Do not use quotes. Just the raw search term.
Example: COSRX Snail Mucin 96% Power Repairing Essence
"""
        response = await self._send_prompt(prompt)
        
        if response:
            return response.strip().replace('"', "")
        return niche
'''

fixed_content = content[:start_idx] + new_method

with open(r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\gemini_web_client.py", "w", encoding="utf-8") as f:
    f.write(fixed_content)
    
print("Fixed gemini_web_client.py!")

import sys

file_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\linktree_client.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find('    async def add_product_to_shop(')
if start_idx == -1:
    print("Could not find start index")
    sys.exit(1)

new_logic = '''    async def add_link(self, title: str, url: str, category: str = None) -> bool:
        """
        Smart Add: Visually checks for the collection, creates it if needed, clicks it, and adds the link.
        """
        logger.info(f"🔗 Linktree: Adding '{title[:50]}' with URL {url[:60]} to collection '{category}'")
        
        page = await self.manager.context.new_page()
        try:
            await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
            await page.wait_for_timeout(8000)
            
            if not category:
                # Add to shop main
                add_btn = page.locator('button:has-text("Add")').first
                await add_btn.click(force=True)
                await page.wait_for_timeout(3000)
                
                linked_btn = page.locator('button:has-text("Linked product")').first
                if await linked_btn.is_visible():
                    await linked_btn.click(force=True)
                    await page.wait_for_timeout(3000)
            else:
                # 1. Check if collection exists
                coll_loc = page.get_by_text(category, exact=True).first
                if not await coll_loc.is_visible():
                    logger.info(f"Collection '{category}' not found visually. Creating it...")
                    add_btn = page.locator('button:has-text("Add")').first
                    await add_btn.click(force=True)
                    await page.wait_for_timeout(2000)
                    
                    coll_btn = page.locator('button:has-text("collection"), button:has-text("Collection")').first
                    await coll_btn.click(force=True)
                    await page.wait_for_timeout(3000)
                    
                    title_input = page.locator('input[placeholder*="Name"], input[name="title"], input[type="text"]').first
                    await title_input.fill(category)
                    await page.wait_for_timeout(1000)
                    await page.keyboard.press("Enter")
                    
                    continue_btn = page.locator('button:has-text("Continue"), button:has-text("Save"), button:has-text("Create")').first
                    if await continue_btn.is_visible():
                        await continue_btn.click(force=True)
                        
                    logger.info("Waiting 10 seconds for Linktree to save new collection...")
                    await page.wait_for_timeout(10000)
                    
                # 2. Click into the collection
                logger.info(f"Opening collection '{category}'...")
                coll_loc = page.get_by_text(category, exact=True).first
                if not await coll_loc.is_visible():
                    raise Exception(f"Failed to find or create Linktree collection {category}.")
                
                await coll_loc.click(force=True)
                await page.wait_for_timeout(5000)
                
                # 3. Click Add inside collection
                # It might be a giant "Add products to collection +" button or a standard "Add" button
                add_interior = page.locator('text="Add products to collection +", button:has-text("Add")').last
                await add_interior.click(force=True)
                await page.wait_for_timeout(4000)
                
            # 4. Paste URL in search input
            search_input = page.locator('input[placeholder*="Search"], input[placeholder*="paste"], input[type="url"]').first
            await search_input.wait_for(state="visible", timeout=15000)
            
            logger.info(f"Pasting URL: {url[:60]}...")
            await search_input.click(force=True)
            await page.wait_for_timeout(1000)
            await search_input.fill(url)
            
            # 5. Wait for Amazon result
            logger.info("Waiting up to 25 seconds for Amazon search result to load...")
            result_btn = None
            for attempt in range(8):
                await page.wait_for_timeout(3000)
                for btn in await page.locator("button").all():
                    try:
                        txt = (await btn.inner_text()).strip()
                        if "amazon" in txt.lower() and len(txt) > 5 and await btn.is_visible():
                            result_btn = btn
                            break
                    except Exception:
                        pass
                
                if not result_btn:
                    try:
                        last_svg_btn = page.locator("button").filter(has=page.locator("svg")).last
                        if await last_svg_btn.is_visible():
                            result_btn = last_svg_btn
                    except Exception:
                        pass
                        
                if result_btn:
                    break
                    
            if not result_btn:
                raise Exception("No Amazon search result found after 24 seconds.")
                
            logger.info("Clicking Amazon search result...")
            await result_btn.click(force=True)
            await page.wait_for_timeout(4000)
            
            # 6. Save
            continue_save = page.locator('button:has-text("Add product"), button:has-text("Continue"), button:has-text("Save")').first
            if await continue_save.is_visible():
                await continue_save.click(force=True)
                
            logger.info("Waiting 15 seconds for product to save to Linktree...")
            await page.wait_for_timeout(15000)
            
            logger.info("✅ Successfully added product to Linktree!")
            return True
            
        except Exception as e:
            logger.error(f"Linktree Add Link failed: {e}")
            raise Exception(f"Failed to add to Linktree collection {category}. Error: {e}")
        finally:
            await page.close()
'''

new_content = content[:start_idx] + new_logic

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Completely rewrote Linktree add_link logic!")

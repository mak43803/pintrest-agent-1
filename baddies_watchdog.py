"""
BADDIES BEAUTY — PINTEREST & AMAZON AFFILIATE LINK WATCHDOG
=================================================================
Automated Auditor & Commission Integrity Verification Tool.
"""

from __future__ import annotations

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows shell
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

TARGET_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "savvyshop0965-20")
DB_PATH = Path("database/pinterest_ai_agent.db")


def fix_affiliate_link(url: str, target_tag: str) -> str:
    """Ensure the target Amazon affiliate tag is present on the URL."""
    if not url or not url.startswith("http"):
        return url
    if f"tag={target_tag}" in url:
        return url
    if "tag=" in url:
        import re
        url = re.sub(r'tag=[^&]+', f'tag={target_tag}', url)
    else:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}tag={target_tag}"
    return url


def run_watchdog_audit(auto_repair: bool = False, verbose: bool = False) -> dict:
    """Run full DB audit and print formatted Watchdog Report."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at '{DB_PATH}'. Please run the agent first.")
        return {}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query all products
    cursor.execute("""
        SELECT id, product_name, title, category, board_name, status,
               affiliate_link, pin_url, created_at, updated_at
        FROM products
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()

    total_products = len(rows)
    valid_tagged_links = 0
    repaired_links = 0
    missing_links = 0

    fully_published = 0
    pending_linktree = 0
    pins_with_url = 0
    legacy_pins_without_url = 0

    pending_linktree_items = []
    missing_link_items = []
    tag_issues = []

    for row in rows:
        p_id = row["id"]
        title = row["title"] or row["product_name"] or f"Product #{p_id}"
        aff_link = row["affiliate_link"] or ""
        pin_url = row["pin_url"] or ""
        status = row["status"] or ""

        # 1. Link validation & Tag Check
        if not aff_link or not aff_link.startswith("http"):
            missing_links += 1
            missing_link_items.append((p_id, title))
        elif TARGET_TAG in aff_link:
            valid_tagged_links += 1
        else:
            if auto_repair:
                fixed_url = fix_affiliate_link(aff_link, TARGET_TAG)
                cursor.execute("UPDATE products SET affiliate_link = ? WHERE id = ?", (fixed_url, p_id))
                repaired_links += 1
                valid_tagged_links += 1
            else:
                tag_issues.append((p_id, title, aff_link))

        # 2. Publication & Sync Status
        if status.lower() == "published":
            fully_published += 1
        elif status.lower() in ["pinterest_published", "linktree_deferred"]:
            pending_linktree += 1
            pending_linktree_items.append((p_id, title, row["board_name"]))

        # 3. Pin URL tracking check
        if pin_url:
            pins_with_url += 1
        elif status.lower() in ["published", "pinterest_published"]:
            legacy_pins_without_url += 1

    if auto_repair and repaired_links > 0:
        conn.commit()

    conn.close()

    # ═════════════════════════════════════════════════════════════════
    # PRINT FORMATTED WATCHDOG REPORT
    # ═════════════════════════════════════════════════════════════════
    report_lines = [
        "═════════════════════════════════════════════════════════════════",
        " 👑 BADDIES BEAUTY — PINTEREST & AFFILIATE LINK WATCHDOG REPORT",
        "═════════════════════════════════════════════════════════════════",
        f" 🏷️  Target Affiliate Tag : {TARGET_TAG}",
        f" 📦 Total Products in DB : {total_products}",
        f" ✅ Valid Tagged Links   : {valid_tagged_links} / {total_products}",
        f" 🔧 Auto-Repaired Links  : {repaired_links}",
        f" ⚠️  Missing Links        : {missing_links}",
        "─────────────────────────────────────────────────────────────────",
        f" 🌐 Fully Published (Pinterest + Linktree) : {fully_published}",
        f" ⏳ Pending Linktree Sync                 : {pending_linktree}",
        f" 📌 Pins with Saved Pin URL (ID #384-637) : {pins_with_url}",
        f" 📜 Legacy Pins (Older entries #1-383)   : {legacy_pins_without_url}",
        "═════════════════════════════════════════════════════════════════",
    ]

    report = "\n".join(report_lines)
    print("\n" + report + "\n")

    # Save summary report to logs/watchdog_summary.txt for quick user inspection
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/watchdog_summary.txt", "w", encoding="utf-8") as f:
            f.write(report + "\n")
    except Exception:
        pass

    # Detailed breakdown if issues exist or verbose requested
    if pending_linktree_items and verbose:
        print(f"⏳ Pending Linktree Sync Details ({len(pending_linktree_items)} items):")
        for p_id, p_title, p_board in pending_linktree_items[:10]:
            print(f"   • [ID #{p_id}] {p_title[:50]} (Board: {p_board})")
        if len(pending_linktree_items) > 10:
            print(f"   ... and {len(pending_linktree_items) - 10} more items pending Linktree sync.")
        print()

    if tag_issues:
        print(f"⚠️ Tag Mismatch Details ({len(tag_issues)} items):")
        for p_id, p_title, p_link in tag_issues[:5]:
            print(f"   • [ID #{p_id}] {p_title[:50]} -> {p_link[:60]}")
        print("   Tip: Run with '--fix' flag to auto-repair affiliate tags in DB.\n")

    return {
        "total_products": total_products,
        "valid_tagged_links": valid_tagged_links,
        "repaired_links": repaired_links,
        "missing_links": missing_links,
        "fully_published": fully_published,
        "pending_linktree": pending_linktree,
        "pins_with_url": pins_with_url,
        "legacy_pins_without_url": legacy_pins_without_url,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baddies Beauty Affiliate & Pinterest Watchdog")
    parser.add_argument("--fix", action="store_true", help="Auto-repair missing affiliate tags in DB")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed item list for pending syncs")
    args = parser.parse_args()

    run_watchdog_audit(auto_repair=args.fix, verbose=args.verbose)

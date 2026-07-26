import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

scratch_dir = Path("scratch")
if not scratch_dir.exists():
    print("Scratch directory does not exist.")
    sys.exit(0)

deleted_count = 0
freed_bytes = 0

# Keep important fonts or essential test scripts if needed, but remove temporary screenshots, html dumps, and test images
for item in scratch_dir.iterdir():
    if item.is_file():
        ext = item.suffix.lower()
        fname = item.name.lower()
        
        # Delete temporary PNG, JPG, HTML, WEBP, and test scripts
        if ext in (".png", ".html", ".webp") or fname.startswith("dummy_") or fname.startswith("p1_") or fname.startswith("p2_") or fname.startswith("p3_") or fname.startswith("p4_") or fname.startswith("p5_") or fname.startswith("p6_") or fname.startswith("font_test_") or fname.startswith("star_test") or fname.startswith("test_") or fname.startswith("inspect_") or fname.startswith("check_") or fname.startswith("copy_") or fname.startswith("pin_v4_"):
            try:
                sz = item.stat().st_size
                item.unlink()
                deleted_count += 1
                freed_bytes += sz
                print(f"Deleted: {item.name} ({sz/1024:.1f} KB)")
            except Exception as e:
                print(f"Failed to delete {item.name}: {e}")

print(f"\n✅ CLEANUP COMPLETE: Deleted {deleted_count} unwanted temporary files! Freed {freed_bytes / (1024*1024):.2f} MB!")

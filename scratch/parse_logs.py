import re
import sys

# Force stdout to UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

log_path = "logs/agent.log"
print(f"Reading logs from: {log_path}")

failures = []

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        # Standardize characters to avoid print crash
        clean_line = line.replace('\u2502', '|').strip()
        if "Pipeline error" in clean_line or "failed while trying" in clean_line.lower() or "failed!" in clean_line.lower() or "sourcing failed" in clean_line.lower():
            failures.append(clean_line)
        elif "Research failed" in clean_line or "Amazon Sourcing failed" in clean_line or "Pinterest Upload failed" in clean_line:
            failures.append(clean_line)

print(f"\nTotal failure indicators found in logs: {len(failures)}")
print("\n--- Last 30 failure lines in logs: ---")
for line in failures[-30:]:
    print(line)

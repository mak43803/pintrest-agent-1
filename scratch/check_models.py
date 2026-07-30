import os
import urllib.request
import json

print("=== 1. PROJECT CONFIG (.env) ===")
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if any(k in line for k in ["OLLAMA", "GEMINI", "MODEL"]):
                print("  ", line.strip())

print("\n=== 2. LOCAL OLLAMA MODELS ===")
try:
    req = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req, timeout=4) as response:
        data = json.loads(response.read().decode())
        models = data.get("models", [])
        if models:
            for m in models:
                print(f"  - Model Name: {m.get('name')} | Size: {m.get('size', 0) / (1024**3):.2f} GB | Modified: {m.get('modified_at')}")
        else:
            print("  No models currently downloaded in Ollama.")
except Exception as e:
    print(f"  Ollama service status: {e}")

print("\n=== 3. ACTIVE ASSISTANT MODEL ===")
print("  - Primary Cloud AI: Google Gemini 3.6 Flash (High Reasoning & Creative Director)")

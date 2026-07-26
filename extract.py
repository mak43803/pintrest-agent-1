import marshal
import json

def extract_strings(c):
    s = []
    if hasattr(c, 'co_consts'):
        for x in c.co_consts:
            if isinstance(x, str):
                s.append(x)
            if hasattr(x, 'co_consts'):
                s.extend(extract_strings(x))
    return s

with open(r'c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\__pycache__\gemini_web_client.cpython-312.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

strs = extract_strings(code)
for i, string in enumerate(strs):
    if len(string) > 20:
        print(f"--- STRING {i} ---\n{string}\n")

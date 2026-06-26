import os
import re

spiders_dir = r"d:\Projects\hamadema\scraper\lanka_scraper\spiders"
failing_spiders = [
    "tecroot.py", "simplytek.py", "singer.py", "wasi.py", 
    "buyabans.py", "celltronics.py", "dinapalagroup.py", 
    "lifemobile.py", "pettahkade.py", "catchme.py"
]

injection_code = """
    use_playwright = True
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }
"""

for spider_file in failing_spiders:
    filepath = os.path.join(spiders_dir, spider_file)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # If already injected, skip
        if "use_playwright = True" in content:
            print(f"Skipping {spider_file}, already injected.")
            continue
            
        # Inject after allowed_domains
        pattern = r"(allowed_domains\s*=\s*\[.*?\]\n)"
        new_content = re.sub(pattern, r"\1" + injection_code, content, count=1)
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {spider_file}")
    else:
        print(f"File not found: {spider_file}")

# Update takas.py to also have use_playwright = True
takas_path = os.path.join(spiders_dir, "takas.py")
if os.path.exists(takas_path):
    with open(takas_path, 'r') as f:
        content = f.read()
    if "use_playwright = True" not in content:
        pattern = r"(allowed_domains\s*=\s*\[.*?\]\n)"
        new_content = re.sub(pattern, r"\1    use_playwright = True\n", content, count=1)
        with open(takas_path, 'w') as f:
            f.write(new_content)
        print("Updated takas.py")

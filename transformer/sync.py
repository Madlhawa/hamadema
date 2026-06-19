import psycopg2
import meilisearch
from datetime import datetime

import os
import re

def parse_price(price_str):
    if not price_str:
        return 0
    
    if isinstance(price_str, (int, float)):
        return int(price_str)

    # Remove all characters except digits and the decimal point
    cleaned = re.sub(r'[^\d.]', '', str(price_str))
    if cleaned:
        try:
            return int(float(cleaned))
        except ValueError:
            return 0
    return 0

def extract_facets(title):
    title_lower = title.lower()
    facets = {}
    
    # Category
    if "laptop" in title_lower:
        facets["category"] = "Laptop"
    elif "monitor" in title_lower:
        if "arm" in title_lower or "mount" in title_lower:
            facets["category"] = "Monitor Arm"
        elif "gaming" in title_lower:
            facets["category"] = "Gaming Monitor"
        else:
            facets["category"] = "Monitor"
    elif "vga" in title_lower or "graphics card" in title_lower or "rtx" in title_lower or "gtx" in title_lower or "rx " in title_lower:
        facets["category"] = "Graphics Card"
    elif "processor" in title_lower or "cpu" in title_lower or "intel core" in title_lower or "amd ryzen" in title_lower:
        facets["category"] = "Processor"
    elif "motherboard" in title_lower or "mainboard" in title_lower:
        facets["category"] = "Motherboard"
    else:
        facets["category"] = "Other"

    # Brand
    brands = ["asus", "dell", "hp", "lenovo", "acer", "apple", "msi", "gigabyte", "samsung", "lg", "aoc", "viewsonic", "zotac", "corsair", "logitech", "razer"]
    for brand in brands:
        if brand in title_lower.split():
            facets["brand"] = brand.capitalize()
            break
            
    # RAM
    ram_explicit = re.search(r'\b(\d+)\s*(gb)\s*(ram|ddr4|ddr5|lpddr|unified)\b', title_lower)
    if ram_explicit:
        facets["ram"] = f"{ram_explicit.group(1)}GB"
    else:
        # Fallback heuristic for RAM
        ram_match = re.search(r'\b(\d+)\s*(gb|tb)\b', title_lower)
        if ram_match:
            val = ram_match.group(1)
            unit = ram_match.group(2).lower()
            if unit == "gb" and val in ["4", "8", "16", "32", "64"]:
                # Assume RAM if it's a typical RAM size and no storage keywords are adjacent
                if not re.search(r'\b(ssd|hdd|nvme|m\.2)\b', title_lower[max(0, ram_match.start() - 10):ram_match.end() + 10]):
                    facets["ram"] = f"{val}GB"
                    
    # Storage
    storage_match = re.search(r'\b(\d+)\s*(gb|tb)\s*(ssd|hdd|nvme|m\.2|storage)\b', title_lower)
    if storage_match:
        facets["storage"] = f"{storage_match.group(1)}{storage_match.group(2).upper()}"
        
    return facets

# DB Settings
DB_SETTINGS = {
    "dbname": os.environ.get("POSTGRES_DB", "lanka_aggregator"),
    "user": os.environ.get("POSTGRES_USER", "scraper_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "supersecret"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}

# Meilisearch Settings
MEILI_HOST = os.environ.get("MEILI_HOST", "http://localhost:7700")
MEILI_MASTER_KEY = os.environ.get("MEILI_MASTER_KEY", "masterKeyToChange123")

def run_sync():
    print("Starting sync process...")
    try:
        client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
        index = client.index('items')
        
        # Ensure sorting, filtering settings
        index.update_sortable_attributes(['price_numeric'])
        index.update_filterable_attributes(['source_site', 'price_numeric', 'stock_status', 'category', 'brand', 'ram', 'storage'])
        
        # Reset ranking rules to default Meilisearch rules
        index.update_ranking_rules([
            'words',
            'typo',
            'proximity',
            'attribute',
            'sort',
            'exactness'
        ])
    except Exception as e:
        print(f"Could not connect to Meilisearch: {e}")
        return

    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Could not connect to Postgres: {e}")
        return

    cursor.execute("SELECT id, source_site, raw_payload FROM raw_items;")
    rows = cursor.fetchall()

    documents = []
    for row in rows:
        item_id, source, payload = row
        
        title = payload.get("title", f"Unknown Title from {source}")
        price_num = parse_price(payload.get("price", "0"))
        formatted_price = f"Rs. {price_num:,}" if price_num > 0 else "N/A"
        
        facets = extract_facets(title)
        
        doc = {
            "id": str(item_id),
            "source_site": source,
            "title": title,
            "price": formatted_price,
            "price_numeric": price_num,
            "url": payload.get("url", ""),
            "image_url": payload.get("image_url", ""),
            "stock_status": "Out of Stock" if "out" in str(payload.get("stock_status", "")).lower() else "In Stock",
            "synced_at": datetime.utcnow().isoformat(),
            **facets
        }
        documents.append(doc)

    if documents:
        print(f"Pushing {len(documents)} documents to Meilisearch...")
        task = index.add_documents(documents)
        print(f"Task info: {task}")
    else:
        print("No documents to push.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_sync()

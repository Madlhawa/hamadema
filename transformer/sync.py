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
        index.update_filterable_attributes(['source_site', 'price_numeric', 'stock_status'])
        
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
        
        price_num = parse_price(payload.get("price", "0"))
        formatted_price = f"Rs. {price_num:,}" if price_num > 0 else "N/A"
        
        doc = {
            "id": str(item_id),
            "source_site": source,
            "title": payload.get("title", f"Unknown Title from {source}"),
            "price": formatted_price,
            "price_numeric": price_num,
            "url": payload.get("url", ""),
            "image_url": payload.get("image_url", ""),
            "stock_status": "Out of Stock" if "out" in str(payload.get("stock_status", "")).lower() else "In Stock",
            "synced_at": datetime.utcnow().isoformat()
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

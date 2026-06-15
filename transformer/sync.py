import psycopg2
import meilisearch
from datetime import datetime

# DB Settings
DB_SETTINGS = {
    "dbname": "lanka_aggregator",
    "user": "scraper_user",
    "password": "supersecret",
    "host": "localhost",
    "port": "5432",
}

# Meilisearch Settings
MEILI_HOST = "http://localhost:7700"
MEILI_MASTER_KEY = "masterKeyToChange123"

def run_sync():
    print("Starting sync process...")
    try:
        client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
        index = client.index('items')
        
        # Ensure sorting, filtering settings if needed
        # index.update_sortable_attributes(['price'])
        # index.update_filterable_attributes(['source_site'])
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
        doc = {
            "id": str(item_id),
            "source_site": source,
            "title": payload.get("title", f"Unknown Title from {source}"),
            "price": payload.get("price", "N/A"),
            "url": payload.get("url", ""),
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

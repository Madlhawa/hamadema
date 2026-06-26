import psycopg2
import os

DB_SETTINGS = {
    "dbname": os.environ.get("POSTGRES_DB", "lanka_aggregator"),
    "user": os.environ.get("POSTGRES_USER", "scraper_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "supersecret"),
    "host": os.environ.get("POSTGRES_HOST", "postgres"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}

def snapshot_stats():
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cursor = conn.cursor()
        
        # Calculate current counts
        query = """
            SELECT source_site, COUNT(id) as item_count
            FROM raw_items
            GROUP BY source_site;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Insert into historical table
        insert_query = """
            INSERT INTO scraper_stats_history (source_site, item_count, recorded_at)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (source_site, recorded_at)
            DO UPDATE SET item_count = EXCLUDED.item_count;
        """
        
        for row in rows:
            cursor.execute(insert_query, (row[0], row[1]))
            
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Successfully recorded scraper stats snapshot for {len(rows)} stores.")
    except Exception as e:
        print(f"Failed to record scraper stats snapshot: {e}")

if __name__ == "__main__":
    snapshot_stats()

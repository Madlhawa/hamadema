import psycopg2
from psycopg2.extras import Json
from datetime import datetime

class PostgresRawPipeline:
    def __init__(self, db_settings):
        self.db_settings = db_settings

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = crawler.settings.getdict("DB_SETTINGS", {
            "dbname": "lanka_aggregator",
            "user": "scraper_user",
            "password": "supersecret",
            "host": "localhost",
            "port": "5432",
        })
        return cls(db_settings)

    def open_spider(self, spider):
        self.connection = psycopg2.connect(**self.db_settings)
        self.cursor = self.connection.cursor()
        self.create_table_if_not_exists()

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()

    def create_table_if_not_exists(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS raw_items (
            id SERIAL PRIMARY KEY,
            source_site VARCHAR(255) NOT NULL,
            scraped_at TIMESTAMP NOT NULL,
            raw_payload JSONB NOT NULL
        );
        """
        self.cursor.execute(create_table_query)
        self.connection.commit()
        
        # Deduplicate existing rows before creating index
        dedup_query = """
        DELETE FROM raw_items
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_items
            GROUP BY raw_payload->>'url'
        );
        """
        self.cursor.execute(dedup_query)
        self.connection.commit()

        index_query = "CREATE UNIQUE INDEX IF NOT EXISTS raw_items_url_idx ON raw_items ((raw_payload->>'url'));"
        self.cursor.execute(index_query)
        self.connection.commit()

    def process_item(self, item, spider):
        insert_query = """
        INSERT INTO raw_items (source_site, scraped_at, raw_payload)
        VALUES (%s, %s, %s)
        ON CONFLICT ((raw_payload->>'url'))
        DO UPDATE SET scraped_at = EXCLUDED.scraped_at, raw_payload = EXCLUDED.raw_payload;
        """
        source_site = item.get("source_site", "unknown")
        raw_payload = item.get("raw_payload", {})
        scraped_at = datetime.utcnow()

        self.cursor.execute(insert_query, (source_site, scraped_at, Json(raw_payload)))
        self.connection.commit()
        return item

BOT_NAME = "lanka_scraper"

SPIDER_MODULES = ["lanka_scraper.spiders"]
NEWSPIDER_MODULE = "lanka_scraper.spiders"

# --- ANTI-BOT CONFIGURATION (scrapy-impersonate) ---
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

ROBOTSTXT_OBEY = False

# --- PIPELINE CONFIGURATION ---
ITEM_PIPELINES = {
   "lanka_scraper.pipelines.PostgresRawPipeline": 300,
}

import os

DB_SETTINGS = {
    "dbname": os.environ.get("POSTGRES_DB", "lanka_aggregator"),
    "user": os.environ.get("POSTGRES_USER", "scraper_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "supersecret"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}

# Proxy settings
DOWNLOADER_MIDDLEWARES = {
    'lanka_scraper.middlewares.RotatingProxyMiddleware': 100,
}

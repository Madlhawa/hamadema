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

# --- HIGH CONCURRENCY SETTINGS FOR LARGE PROXY POOLS ---
# Send many requests in parallel since we have 100 proxies
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Disable the delay so it scrapes as fast as possible across all IPs
DOWNLOAD_DELAY = 3

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True
BOT_NAME = "lanka_scraper"

SPIDER_MODULES = ["lanka_scraper.spiders"]
NEWSPIDER_MODULE = "lanka_scraper.spiders"

# --- ANTI-BOT CONFIGURATION (scrapy-curl-cffi) ---
DOWNLOAD_HANDLERS = {
    "http": "scrapy_curl_cffi.CurlCffiDownloadHandler",
    "https": "scrapy_curl_cffi.CurlCffiDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

ROBOTSTXT_OBEY = False

# --- PIPELINE CONFIGURATION ---
ITEM_PIPELINES = {
   "lanka_scraper.pipelines.PostgresRawPipeline": 300,
}

DB_SETTINGS = {
    "dbname": "lanka_aggregator",
    "user": "scraper_user",
    "password": "supersecret",
    "host": "localhost",
    "port": "5432",
}

# Proxy settings
# PROXY_URL = "http://username:password@proxyserver.com:8080"

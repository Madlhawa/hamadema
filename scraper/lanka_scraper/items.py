import scrapy

class LankaScraperItem(scrapy.Item):
    source_site = scrapy.Field()
    raw_payload = scrapy.Field()

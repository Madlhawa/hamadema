import scrapy
from scrapy.http import Request

class BaseSpider(scrapy.Spider):
    name = "base_spider"
    
    def start_requests(self):
        urls = [
            "https://httpbin.org/headers", # Test URL to verify curl-cffi
        ]
        for url in urls:
            yield Request(
                url=url, 
                callback=self.parse,
                meta={
                    "impersonate": "chrome110"
                }
            )

    def parse(self, response):
        yield {
            "source_site": "httpbin_test",
            "raw_payload": {
                "url": response.url,
                "body": response.text, 
                "status": response.status
            }
        }

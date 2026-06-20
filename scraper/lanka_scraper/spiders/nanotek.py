import scrapy
from scrapy import Request

class NanotekSpider(scrapy.Spider):
    name = "nanotek"
    allowed_domains = ["nanotek.lk"]
    def start_requests(self):
        # Start at the homepage to dynamically extract category links
        yield Request(
            url="https://www.nanotek.lk/",
            callback=self.parse_homepage,
            meta={
                "impersonate": "chrome116"
            }
        )

    def parse_homepage(self, response):
        category_links = set()
        for href in response.css('a::attr(href)').getall():
            if '/category/' in href:
                category_links.add(response.urljoin(href))
                
        for url in category_links:
            yield Request(
                url=url,
                callback=self.parse,
                meta={
                    "impersonate": "chrome116"
                }
            )

    def parse(self, response):
        # Find all product blocks
        products = response.css('.ty-productBlock')
        for product in products:
            # The URL is stored in the <a> tag wrapping the product block
            url = product.xpath('ancestor::a/@href').get()
            
            # Extract basic product details
            title = product.css('.ty-productBlock-title h1::text').get()
            price = product.css('.ty-productBlock-price-retail::text').get()
            category = product.css('.ty-productBlock-cat::text').get()
            image = product.css('.ty-productBlock-imgHolder img::attr(src)').get()
            stock_msg = product.css('.ty-productBlock-specialMsg span::text').get()

            # Clean up the text data
            title = title.strip() if title else ""
            price = price.strip() if price else ""
            stock_msg = stock_msg.strip() if stock_msg else ""
            
            # Construct the raw JSONB payload
            raw_payload = {
                "title": title,
                "price": price,
                "url": url,
                "image_url": image,
                "category": category,
                "stock_status": stock_msg
            }
            
            # Yield to the PostgresRawPipeline
            yield {
                "source_site": "nanotek.lk",
                "raw_payload": raw_payload
            }
            
        # Handle Pagination (Find the "Next Page" button)
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield Request(
                url=next_page,
                callback=self.parse,
                meta={
                    "impersonate": "chrome116"
                }
            )

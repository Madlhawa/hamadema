import scrapy
from scrapy.http import Request

class MySoftlogicSpider(scrapy.Spider):
    name = "mysoftlogic"
    allowed_domains = ["mysoftlogic.lk"]
    start_urls = [
        "https://mysoftlogic.lk/"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, meta={"impersonate": "chrome116"})

    def parse(self, response):
        category_links = set()
        
        for href in response.css('a::attr(href)').getall():
            if '/c/' in href:
                category_links.add(href)
                
        for url in category_links:
            if url.startswith('/'):
                full_url = 'https://mysoftlogic.lk' + url
            else:
                full_url = url
                
            # Extract category name
            cat_name = url.split('/c/')[0].split('/')[-1].replace('-', ' ').title()
            
            yield Request(
                url=full_url, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": cat_name}
            )

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
        products = response.css(".product_item")
        
        for product in products:
            title = product.css(".product_name a::attr(title)").get()
            if not title:
                title = product.css(".product_name a::text").get()
                
            price_text = product.css(".product_price::attr(data-price)").get()
            
            url = product.css(".product_name a::attr(href)").get()
            if url and url.startswith('/'):
                url = 'https://mysoftlogic.lk' + url
                
            image_url = product.css(".product_image img::attr(src)").get()
            
            in_stock = True

            if title and price_text:
                price_clean_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
                try:
                    price_clean = float(price_clean_str)
                except ValueError:
                    price_clean = 0.0

                if price_clean > 0:
                    raw_payload = {
                        "title": title.strip(),
                        "price": price_clean,
                        "url": url,
                        "image_url": image_url,
                        "category": category,
                        "in_stock": in_stock,
                        "stock_status": "In Stock" if in_stock else "Out of Stock",
                        "store": "MySoftlogic",
                    }
                    
                    yield {
                        "source_site": "mysoftlogic.lk",
                        "raw_payload": raw_payload
                    }

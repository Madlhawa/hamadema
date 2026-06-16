import scrapy
from scrapy.http import Request

class BigDealsSpider(scrapy.Spider):
    name = "bigdeals"
    allowed_domains = ["bigdeals.lk"]
    start_urls = [
        "https://bigdeals.lk/smartphones",
        "https://bigdeals.lk/dekstops-and-pc",
        "https://bigdeals.lk/laptops",
        "https://bigdeals.lk/home-appliances",
        "https://bigdeals.lk/electronic-devices",
    ]

    def parse(self, response):
        products = response.css(".product-container")
        for product in products:
            title = product.css(".product-title::text").get()
            price_text = product.css(".product-price::text").get()
            url = product.css(".left-block a::attr(href)").get()
            image_url = product.css("img.grid-product::attr(data-src)").get()
            
            # Check stock
            btn_text = product.css(".btn-mall::text").get()
            in_stock = True if (btn_text and "Buy Now" in btn_text) else False

            if title and price_text:
                price_clean = float(price_text.replace("Rs", "").replace(",", "").strip())
                
                raw_payload = {
                    "title": title.strip(),
                    "price": price_clean,
                    "url": url,
                    "image_url": image_url,
                    "in_stock": in_stock,
                    "stock_status": "In Stock" if in_stock else "Out of Stock",
                    "store": "Bigdeals",
                }
                
                yield {
                    "source_site": "bigdeals.lk",
                    "raw_payload": raw_payload
                }

        # Pagination
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield Request(url=next_page, callback=self.parse)

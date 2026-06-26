import scrapy
from scrapy.http import Request

class DinapalagroupSpider(scrapy.Spider):
    name = "dinapalagroup"
    allowed_domains = ["dinapalagroup.lk"]

    use_playwright = True
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }
    start_urls = ["https://dinapalagroup.lk/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, meta={"impersonate": "chrome116"})

    def parse(self, response):
        category_links = set()
        
        # Extract category links
        for href in response.css('a::attr(href)').getall():
            if '/product-category/' in href:
                category_links.add(href)
                
        for url in category_links:
            # Extract category name from URL path
            parts = url.strip('/').split('/')
            cat_name = parts[-1].replace('-', ' ').title()
            
            yield Request(
                url=url, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": cat_name}
            )

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
        products = response.css("ul.products li.product")
        
        for product in products:
            title = product.css(".woocommerce-loop-product__title::text").get()
            if not title:
                title = product.css("h2::text").get()
                
            price_text = product.css(".price .amount::text").getall()
            if price_text:
                price_text = price_text[-1]
            else:
                price_text = "0"
                
            url = product.css("a.woocommerce-LoopProduct-link::attr(href)").get()
            if not url:
                url = product.css("a::attr(href)").get()
                
            image_url = product.css("img.attachment-woocommerce_thumbnail::attr(src)").get()
            if not image_url:
                image_url = product.css("img::attr(src)").get()

            # Out of stock check
            in_stock = True
            if product.css(".outofstock"):
                in_stock = False

            if title and url:
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
                        "store": "Dinapala Group",
                    }
                    
                    yield {
                        "source_site": "dinapalagroup.lk",
                        "raw_payload": raw_payload
                    }
                    
        # Pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield Request(
                url=next_page,
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": category}
            )

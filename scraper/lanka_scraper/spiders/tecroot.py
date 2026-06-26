import scrapy
from scrapy.http import Request

class TecrootSpider(scrapy.Spider):
    name = "tecroot"
    allowed_domains = ["tecroot.lk"]

    use_playwright = True
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }
    start_urls = [
        "https://tecroot.lk/"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, meta={"impersonate": "chrome116"})

    def parse(self, response):
        category_links = set()
        
        # Grab hrefs that match product-category layout
        for href in response.css('a::attr(href)').getall():
            if href.startswith('https://tecroot.lk/product-category/') and '/page/' not in href:
                category_links.add(href)
                
        for url in category_links:
            cat_name = url.split('/product-category/')[1].split('/')[0].replace('-', ' ').title()
            yield Request(
                url=url, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": cat_name}
            )

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
        products = response.css(".product")
        for product in products:
            title = product.css(".woocommerce-loop-product__title::text").get()
            price_text = product.css(".woocommerce-Price-amount bdi::text").getall()
            
            # Use the last price text in case there's a strikethrough original price
            price_str = price_text[-1] if price_text else None
            if not price_str:
                # Fallback if bdi is not used
                price_text = product.css(".price::text").getall()
                # filter out empty strings
                price_text = [p.strip() for p in price_text if p.strip()]
                price_str = price_text[-1] if price_text else None
            
            url = product.css(".woocommerce-LoopProduct-link::attr(href)").get()
            if not url:
                url = product.css("a::attr(href)").get()
            
            # Sometimes WooCommerce uses lazy loading so we look for data-src or src
            image_url = product.css("img.attachment-woocommerce_thumbnail::attr(data-src)").get()
            if not image_url:
                image_url = product.css("img.attachment-woocommerce_thumbnail::attr(src)").get()
                
            # Check stock
            stock_class = product.attrib.get('class', '')
            in_stock = 'outofstock' not in stock_class

            if title and price_str:
                # Keep numeric parts and decimals
                price_clean_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
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
                        "store": "TecRoot",
                    }
                    
                    yield {
                        "source_site": "tecroot.lk",
                        "raw_payload": raw_payload
                    }

        # Pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield Request(
                url=next_page, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": category}
            )

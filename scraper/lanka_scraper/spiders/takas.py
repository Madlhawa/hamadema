import scrapy
from scrapy.http import Request
from scrapy_playwright.page import PageMethod

class TakasSpider(scrapy.Spider):
    name = "takas"
    allowed_domains = ["takas.lk"]
    use_playwright = True

    # Playwright requires its own handler, overriding the global impersonate handler
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }

    # 1. Define your bypass settings as class variables so they are reusable
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    playwright_bypass_meta = {
        "playwright": True,
        "handle_httpstatus_list": [403],
        "playwright_page_init_scripts": [
            {"path": "stealth.min.js"}
        ],
        "playwright_page_methods": [
            PageMethod("wait_for_timeout", 8000), 
        ]
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://takas.lk/", 
            callback=self.parse,
            headers=self.custom_headers,
            meta=self.playwright_bypass_meta
        )

    def parse(self, response):
        category_links = set()
        
        # Extract category links from the top navigation menu
        for href in response.css('a.nav-a::attr(href)').getall():
            if href.endswith('.html') and '?' not in href:
                category_links.add(href)
                
        for url in category_links:
            parts = url.replace('https://takas.lk/', '').replace('.html', '').split('/')
            cat_name = parts[-1].replace('-', ' ').title()
            if cat_name.lower() in ["offers", "deals"]:
                continue
            
            # 2. Copy the bypass meta and add your category tag
            req_meta = self.playwright_bypass_meta.copy()
            req_meta["category"] = cat_name
                
            yield Request(
                url=url, 
                callback=self.parse_category,
                headers=self.custom_headers, # Keep the human User-Agent
                meta=req_meta                # Keep Playwright engaged
            )

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
        products = response.css(".item")
        
        for product in products:
            title = product.css(".product-name a::attr(title)").get()
            if not title:
                title = product.css(".product-name a::text").get()
                
            price_text = product.css(".price-box .price::text").get()
            if not price_text:
                # Sometimes there's a special price
                price_text = product.css(".special-price .price::text").get()
                
            url = product.css(".product-name a::attr(href)").get()
            image_url = product.css(".product-image img::attr(src)").get()
            
            # Magento typical availability check. Let's assume in_stock=True for now, 
            # unless out-of-stock class is present
            in_stock = True
            if product.css(".out-of-stock"):
                in_stock = False

            if title and price_text and url:
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
                        "store": "Takas",
                    }
                    
                    yield {
                        "source_site": "takas.lk",
                        "raw_payload": raw_payload
                    }
                    
        # Pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            # 3. Keep the bypass meta going for the next pages
            req_meta = self.playwright_bypass_meta.copy()
            req_meta["category"] = category
            
            yield Request(
                url=next_page,
                callback=self.parse_category,
                headers=self.custom_headers,
                meta=req_meta
            )
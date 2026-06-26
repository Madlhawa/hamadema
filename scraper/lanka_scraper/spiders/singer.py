import scrapy
from scrapy.http import Request

class SingerSpider(scrapy.Spider):
    name = "singer"
    allowed_domains = ["singersl.com"]

    use_playwright = True
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }
    start_urls = ["https://www.singersl.com/products/electronics"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_homepage_categories, meta={"impersonate": "chrome116"})

    def parse_homepage_categories(self, response):
        # Find all category links in the electronics submenu or dropdowns
        category_links = set()
        for href in response.css("a::attr(href)").getall():
            if 'https://www.singersl.com/products/' in href:
                category_links.add(href)
                
        for url in category_links:
            # Extract category name from URL path
            parts = url.split('/')
            cat_name = parts[-1].replace('-', ' ').title()
            
            yield Request(
                url=url, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": cat_name}
            )

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
        
        # Scrape all product containers on the page
        products = response.css(".productfilter")
        
        for product in products:
            # Title is typically in a title attribute of the image or the anchor link
            title = product.css("img.card-img-top::attr(title)").get()
            if not title:
                title = product.css("a::attr(title)").get()
                
            url = product.css("a::attr(href)").get()
            image_url = product.css("img.card-img-top::attr(src)").get()
            
            price_text = product.css(".price::text").get()
            if not price_text:
                price_text = product.css(".product__price::text").get()
                
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
                        "in_stock": True, # Assume true since they list them
                        "stock_status": "In Stock",
                        "store": "Singer",
                    }
                    
                    yield {
                        "source_site": "singersl.com",
                        "raw_payload": raw_payload
                    }
        
        # Singer usually uses lazy load or no pagination if everything is pre-loaded on the server side HTML.
        # But we'll try to find a next link just in case
        next_page = response.css("a.next::attr(href), a.page-link[rel='next']::attr(href)").get()
        if next_page:
            if not next_page.startswith('http'):
                next_page = response.urljoin(next_page)
            yield Request(
                url=next_page,
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": category}
            )

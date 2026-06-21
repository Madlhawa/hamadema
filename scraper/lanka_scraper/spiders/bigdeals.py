import scrapy
from scrapy.http import Request

class BigDealsSpider(scrapy.Spider):
    name = "bigdeals"
    allowed_domains = ["bigdeals.lk"]
    start_urls = [
        "https://bigdeals.lk/"
    ]

    def parse(self, response):
        category_links = set()
        
        # Look in known menu containers
        for href in response.css('nav a::attr(href), .menu a::attr(href), .vertical-menu-list a::attr(href), .categories a::attr(href)').getall():
            if href.startswith('https://bigdeals.lk/') and len(href.split('/')) == 4:
                category_links.add(href)
                
        # Also grab any hrefs matching the pattern just in case
        for href in response.css('a::attr(href)').getall():
            if href.startswith('https://bigdeals.lk/') and len(href.split('/')) == 4:
                # filter out obvious non-categories
                if not any(x in href for x in ['login', 'contact', 'policy', 'about', 'terms', 'cart', 'checkout']):
                    category_links.add(href)

        for url in category_links:
            cat = url.rstrip('/').split('/')[-1]
            cat_name = cat.replace('-', ' ').title()
            yield Request(url=url, callback=self.parse_category, meta={"category": cat_name})

    def parse_category(self, response):
        category = response.meta.get("category", "Other")
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
                    "category": category,
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
            yield Request(url=next_page, callback=self.parse_category, meta={"category": category})

import scrapy
from scrapy.http import Request

class TakasSpider(scrapy.Spider):
    name = "takas"
    allowed_domains = ["takas.lk"]
    start_urls = ["https://takas.lk/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, meta={"impersonate": "chrome116"})

    def parse(self, response):
        category_links = set()
        
        # Extract category links from the top navigation menu
        for href in response.css('a.nav-a::attr(href)').getall():
            if href.endswith('.html') and '?' not in href:
                category_links.add(href)
                
        for url in category_links:
            # Extract category name
            parts = url.replace('https://takas.lk/', '').replace('.html', '').split('/')
            cat_name = parts[-1].replace('-', ' ').title()
            if cat_name.lower() in ["offers", "deals"]:
                continue
                
            yield Request(
                url=url, 
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": cat_name}
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
            yield Request(
                url=next_page,
                callback=self.parse_category,
                meta={"impersonate": "chrome116", "category": category}
            )

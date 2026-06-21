import scrapy
from scrapy.http import Request

class MydealzSpider(scrapy.Spider):
    name = "mydealz"
    allowed_domains = ["mydealz.lk"]
    start_urls = [
        "https://www.mydealz.lk/"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, meta={"impersonate": "chrome116"})

    def parse(self, response):
        category_links = set()
        
        # Look for category links
        for href in response.css('a::attr(href)').getall():
            if href.startswith('https://www.mydealz.lk/product-category/') and '/page/' not in href:
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
            
            # Extract price: WooCommerce often uses `<span class="woocommerce-Price-amount amount"><bdi>`
            price_text = product.css(".woocommerce-Price-amount bdi::text").getall()
            price_str = price_text[-1] if price_text else None
            if not price_str:
                price_text = product.css(".price::text").getall()
                price_text = [p.strip() for p in price_text if p.strip()]
                price_str = price_text[-1] if price_text else None
                
            url = product.css(".woocommerce-LoopProduct-link::attr(href)").get()
            if not url:
                url = product.css("a::attr(href)").get()
                
            image_url = product.css("img.attachment-woocommerce_thumbnail::attr(data-lazy-src)").get()
            if not image_url:
                image_url = product.css("img.attachment-woocommerce_thumbnail::attr(src)").get()
                
            stock_class = product.attrib.get('class', '')
            in_stock = 'outofstock' not in stock_class

            if title and price_str:
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
                        "store": "MyDealz",
                    }
                    
                    yield {
                        "source_site": "mydealz.lk",
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

import scrapy
from scrapy import Request

class WasiSpider(scrapy.Spider):
    name = "wasi"
    allowed_domains = ["wasi.lk"]
    start_urls = [
        "https://www.wasi.lk/product-category/computers-laptops/laptops/",
        "https://www.wasi.lk/product-category/mobile-phones/smartphones/",
        "https://www.wasi.lk/product-category/electronic-devices/monitors/",
        "https://www.wasi.lk/product-category/electronic-devices/keyboards-mouse/"
    ]


    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta={"impersonate": "chrome120"}
            )

    def parse(self, response):
        # Find all product blocks in WooCommerce layout
        products = response.css('li.product')
        for product in products:
            # Extract basic product details
            title = product.css('.woo-loop-product__title a::text').get()
            url = product.css('.woo-loop-product__title a::attr(href)').get()
            
            # Wasi uses mf-product-thumbnail img for images
            image = product.css('.mf-product-thumbnail img::attr(src)').get()
            
            # Price can be tricky if it has "Starting" text or multiple prices (e.g. sale vs regular)
            # We try to get the .wasi-archive-price first, then fallback to standard .price
            price_raw = product.css('.wasi-archive-price::text').get()
            if not price_raw:
                # Sometimes WooCommerce uses standard ins/del for prices
                price_raw = product.css('.price ins .woocommerce-Price-amount::text').get()
                if not price_raw:
                    price_raw = product.css('.price .woocommerce-Price-amount::text').get()
            
            # Stock status
            out_of_stock_tag = product.css('.out-of-stock.ribbon::text').get()
            stock_msg = "Out of Stock" if out_of_stock_tag else "In Stock"

            # Clean up the text data
            title = title.strip() if title else ""
            price = price_raw.strip() if price_raw else ""
            
            # Categories can be parsed from URL or simply by the requested category
            # Let's derive a simple category from the URL
            category = ""
            if "laptops" in response.url:
                category = "Laptops"
            elif "smartphones" in response.url:
                category = "Smartphones"
            elif "monitors" in response.url:
                category = "Monitors"
            elif "keyboards-mouse" in response.url:
                category = "Peripherals"

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
                "source_site": "wasi.lk",
                "raw_payload": raw_payload
            }
            
        # Handle Pagination (Find the "Next Page" button)
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield Request(
                url=next_page,
                callback=self.parse,
                meta={"impersonate": "chrome120"}
            )

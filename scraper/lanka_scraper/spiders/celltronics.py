import scrapy
import json

class CelltronicsSpider(scrapy.Spider):
    name = "celltronics"
    allowed_domains = ["celltronics.lk"]

    use_playwright = True
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        }
    }

    def start_requests(self):
        url = "https://celltronics.lk/products.json?limit=250&page=1"
        yield scrapy.Request(url=url, callback=self.parse, meta={"page": 1})

    def parse(self, response):
        data = json.loads(response.text)
        products = data.get("products", [])
        
        if not products:
            return

        for product in products:
            title = product.get("title")
            url = f"https://celltronics.lk/products/{product.get('handle')}"
            
            # Extract category
            category = product.get("product_type", "Electronics")
            if not category and product.get("tags"):
                category = product.get("tags")[0]

            # Extract image
            images = product.get("images", [])
            image_url = images[0].get("src") if images else ""

            # Extract price and stock from variants
            variants = product.get("variants", [])
            if variants:
                variant = variants[0]
                price = variant.get("price")
                in_stock = variant.get("available", False)
                
                try:
                    price_clean = float(price)
                except (ValueError, TypeError):
                    price_clean = 0.0

                if title and price_clean > 0:
                    raw_payload = {
                        "title": title.strip(),
                        "price": price_clean,
                        "url": url,
                        "image_url": image_url,
                        "category": category,
                        "in_stock": in_stock,
                        "stock_status": "In Stock" if in_stock else "Out of Stock",
                        "store": "Celltronics",
                    }

                    yield {
                        "source_site": "celltronics.lk",
                        "raw_payload": raw_payload
                    }

        # Handle pagination
        if len(products) == 250:
            current_page = response.meta["page"]
            next_page = current_page + 1
            next_url = f"https://celltronics.lk/products.json?limit=250&page={next_page}"
            yield scrapy.Request(url=next_url, callback=self.parse, meta={"page": next_page})

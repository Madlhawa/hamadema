import os
import random
import logging
from scrapy_playwright.page import PageMethod

class RotatingProxyMiddleware:
    """
    Middleware that reads a list of proxies from a proxies.txt file 
    in Webshare's default IP:PORT:USERNAME:PASSWORD format
    and randomly assigns one to each request.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        
        # Look for proxies.txt in the current directory (should be the scraper directory)
        proxy_file = os.path.join(os.getcwd(), 'proxies.txt')
        
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Webshare format: IP:PORT:USERNAME:PASSWORD
                    parts = line.split(':')
                    if len(parts) == 4:
                        ip, port, username, password = parts
                        # Scrapy expects: http://username:password@ip:port
                        formatted_proxy = f"http://{username}:{password}@{ip}:{port}"
                        self.proxies.append(formatted_proxy)
                    else:
                        self.logger.warning(f"Skipping incorrectly formatted proxy line: {line}")
                        
            self.logger.info(f"Loaded {len(self.proxies)} proxies from {proxy_file}")
        else:
            self.logger.warning(f"No proxies.txt file found at {proxy_file}. Requests will not be proxied.")

    def process_request(self, request, spider):
        # Check if the spider opted into Playwright
        use_playwright = getattr(spider, 'use_playwright', False)
        
        if use_playwright:
            request.meta['playwright'] = True

            # Handle HTTP 403 responses to allow Playwright to retry
            request.meta['handle_httpstatus_list'] = [403]

            # Inject stealth evasion script for Cloudflare
            request.meta['playwright_page_init_scripts'] = [
                {"path": "/opt/app/scraper/stealth.min.js"}
            ]
            
            # Inject 8-second delay to bypass Turnstile/Cloudflare challenges
            existing_methods = request.meta.get('playwright_page_methods', [])
            # Avoid appending it twice if the spider already defined it
            if not any(m.method == "wait_for_timeout" for m in existing_methods):
                existing_methods.append(PageMethod("wait_for_timeout", 8000))
            request.meta['playwright_page_methods'] = existing_methods
        else:
            # Default to impersonate for lightweight scraping
            request.meta['impersonate'] = 'chrome110'

        if not self.proxies:
            return

        # Choose a random proxy
        proxy = random.choice(self.proxies)
        
        if use_playwright:
            # Playwright uses a special context argument for proxies
            try:
                # proxy format: http://username:password@ip:port
                auth_part, ip_port = proxy.replace('http://', '').split('@')
                username, password = auth_part.split(':')
                
                context_kwargs = request.meta.get('playwright_context_kwargs', {})
                context_kwargs['proxy'] = {
                    "server": f"http://{ip_port}",
                    "username": username,
                    "password": password
                }
                context_kwargs['ignore_https_errors'] = True
                
                # Omit User-Agent to let Playwright use its default real Chromium User-Agent,
                # or use a modern hardcoded one so Cloudflare doesn't block the Scrapy default UA.
                context_kwargs['user_agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    
                request.meta['playwright_context_kwargs'] = context_kwargs
                self.logger.debug(f"Using Playwright proxy for {request.url}")
            except Exception as e:
                self.logger.error(f"Failed to parse Playwright proxy: {e}")
        else:
            # Standard Scrapy Impersonate proxy format
            request.meta['proxy'] = proxy
            self.logger.debug(f"Using Impersonate proxy {proxy} for {request.url}")

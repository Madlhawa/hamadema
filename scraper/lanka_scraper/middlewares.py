import os
import random
import logging

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
        if not self.proxies:
            return

        # Choose a random proxy
        proxy = random.choice(self.proxies)
        
        # Assign to request meta
        request.meta['proxy'] = proxy
        self.logger.debug(f"Using proxy {proxy} for {request.url}")

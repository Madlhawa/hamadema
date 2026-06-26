# Hybrid Playwright & Impersonate Spider Migration

We have successfully migrated the failing spiders to the highly evasive Playwright engine while preserving the lightweight `scrapy-impersonate` engine for the spiders that don't need it.

## What Was Done

### 1. Smart Proxy Middleware
I completely rewrote the `RotatingProxyMiddleware` in `scraper/lanka_scraper/middlewares.py`. 
It is now fully "engine aware":
- **Playwright Spiders**: It dynamically formats your Webshare proxies specifically for the Playwright Chromium context, injects the `stealth.min.js` script automatically using an absolute path (`/opt/app/scraper/stealth.min.js`), and ignores HTTPS proxy errors.
- **Impersonate Spiders**: It uses standard Scrapy proxy formatting and injects the `chrome110` TLS fingerprint.

### 2. Automatic Playwright Upgrades
Instead of manually copying the Playwright configuration into 11 different files and manually updating hundreds of `scrapy.Request` yields, I wrote a script that injected a simple configuration block into the top of all 11 failing spiders (`tecroot`, `simplytek`, `singer`, `wasi`, `buyabans`, `celltronics`, `dinapalagroup`, `lifemobile`, `pettahkade`, `catchme`, and `takas`).

Because of the new Smart Middleware, all these spiders now automatically spin up headless Chrome, inject stealth scripts, and bypass Cloudflare without you having to change a single line of their parsing logic!

### 3. Server Safety
Because we kept `bigdeals`, `nanotek`, `redlinetech`, `mysoftlogic`, and `mydealz` on the `scrapy-impersonate` engine, your server memory usage will remain perfectly stable. Playwright will only launch when Airflow schedules the failing bots, keeping maximum concurrent Chrome tabs extremely low.

All changes have been committed and pushed to `main`!

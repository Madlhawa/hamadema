# 6-Site Scraper Expansion Implementation Plan

The user has requested to add scrapers for 7 sites. Since `mysoftlogic.lk` was already completed in our previous session, we have 6 remaining targets:
1. `https://buyabans.com/`
2. `https://catchme.lk/`
3. `https://dinapalagroup.lk/`
4. `https://lifemobile.lk/`
5. `https://pettahkade.lk/`
6. `https://celltronics.lk/`

## Platform Analysis & Proposed Changes

I ran diagnostic tests against all 6 targets to identify their backend architectures, allowing us to build the most efficient scraper for each:

### 1. Shopify APIs (Fast & Robust)
**Targets**: `buyabans.com`, `celltronics.lk`
**Strategy**: Both sites are built on Shopify. We will bypass scraping their HTML entirely and hit their public `/products.json` API endpoints directly. This is extremely fast and guarantees 100% data accuracy for titles, prices, images, and inventory statuses.

### 2. WooCommerce DOM Parsing
**Targets**: `dinapalagroup.lk`, `lifemobile.lk`, `pettahkade.lk`
**Strategy**: All three are built on WooCommerce. We will build standard Scrapy DOM parsers using reliable WooCommerce selectors (`ul.products li.product`, `.woocommerce-loop-product__title`, `.price .amount`). The spiders will start at their homepages, dynamically discover categories, and follow pagination.

### 3. Custom / Cloudflare Protection
**Target**: `catchme.lk`
**Strategy**: Catchme uses strict Cloudflare protection that blocks standard requests (HTTP 403). We will build a custom Scrapy spider that utilizes `scrapy-impersonate` with a `chrome116` TLS fingerprint to bypass the bot-protection, parse the DOM, and extract the catalog.

### 4. Airflow DAG Optimization
We must adhere to the architectural constraint: *"Please run only two scraper parallely in the dag"*.
We will add these 6 new tasks sequentially to the end of our 2 existing Airflow branches:
- **Branch 1 Sequence (+3)**: `... >> wasi_spider >> buyabans_spider >> celltronics_spider >> dinapalagroup_spider >> data_transformer`
- **Branch 2 Sequence (+3)**: `... >> singer_spider >> lifemobile_spider >> pettahkade_spider >> catchme_spider >> data_transformer`

This ensures that despite managing 16 different store scrapers in total, the server will **never** execute more than 2 at the same time.

## User Review Required
Does this strategy align with your expectations? If approved, I will begin coding the 6 new spiders and modifying the pipeline!

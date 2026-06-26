# Daily Indexed Items Graph & Analytics Upgrade

We have successfully implemented the automated, historically-accurate daily snapshot system for your scraped items!

## Architecture Changes

### The Snapshot Script (`transformer/snapshot_stats.py`)
We built a lightweight Python utility that securely connects directly to your Postgres database and calculates the absolute `COUNT()` of items per store inside the `raw_items` table. It then securely inserts this snapshot into a brand new `scraper_stats_history` table stamped with `CURRENT_DATE`.

### Airflow Pipeline Integration (`dags/scraping_pipeline.py`)
Rather than relying on hacky backend requests, we elegantly wired the `snapshot_stats.py` script directly into your Airflow DAG as a new `BashOperator` task named `record_scraper_stats`. 

This task is configured to run at the absolute end of the pipeline—immediately after `run_data_transformer` finishes pushing everything to Meilisearch. This guarantees that your historical metrics are recorded exactly when they are fresh.

### Admin Dashboard Enhancements (`backend/app.py` & `admin.html`)
The backend now queries the `scraper_stats_history` table for the last 7 days. It restructures the data and passes it to the `admin.html` template, where we implemented a beautiful **stacked bar chart** using Chart.js.

The chart instantly color-codes and stacks each store's inventory, giving you a crystal-clear visual of your daily scraping performance over the past week!

All code has been committed to the `main` branch.

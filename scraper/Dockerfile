FROM python:3.10-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Setup cron job (runs every 6 hours)
RUN echo "0 */6 * * * root cd /app && scrapy crawl base_spider > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron
RUN crontab /etc/cron.d/scraper-cron

# Export environment variables so cron jobs can see them
RUN echo '#!/bin/sh' > /app/run.sh && \
    echo 'env >> /etc/environment' >> /app/run.sh && \
    echo 'cron -f' >> /app/run.sh && \
    chmod +x /app/run.sh

CMD ["/app/run.sh"]

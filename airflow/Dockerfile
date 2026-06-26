FROM apache/airflow:2.9.0-python3.10

USER root
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install Playwright browser binary (Chromium)
RUN python -m playwright install chromium

USER root
# Install Playwright system dependencies
RUN python -m playwright install-deps chromium
USER airflow

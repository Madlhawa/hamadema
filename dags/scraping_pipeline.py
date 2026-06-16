from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'lanka_aggregator_pipeline',
    default_args=default_args,
    description='Runs Scrapy spider and Meilisearch transformer',
    schedule_interval='0 */6 * * *',  # Run every 6 hours
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['scraping'],
) as dag:

    # Task 1: Run the Nanotek Scrapy Spider
    run_nanotek = BashOperator(
        task_id='run_nanotek_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl nanotek',
    )

    # Task 2: Run the Wasi Scrapy Spider
    run_bigdeals_spider = BashOperator(
        task_id='run_bigdeals_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl bigdeals',
    )

    # Task 3: Run the Transformer script
    run_data_transformer = BashOperator(
        task_id='run_data_transformer',
        bash_command='cd /opt/app/transformer && python sync.py',
    )

    # Define execution order
    [run_nanotek, run_bigdeals_spider] >> run_data_transformer

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pendulum

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
    schedule_interval='0 0 * * *',  # Run once a day at midnight (timezone-aware)
    start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Colombo"),
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

    # Task 3: Run the TecRoot Scrapy Spider
    run_tecroot_spider = BashOperator(
        task_id='run_tecroot_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl tecroot',
    )

    # Task 4: Run the Redline Scrapy Spider
    run_redline_spider = BashOperator(
        task_id='run_redline_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl redline',
    )

    # Task 5: Run the MyDealz Scrapy Spider
    run_mydealz_spider = BashOperator(
        task_id='run_mydealz_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl mydealz',
    )

    # Task 6: Run the MySoftlogic Scrapy Spider
    run_mysoftlogic_spider = BashOperator(
        task_id='run_mysoftlogic_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl mysoftlogic',
    )

    # Task 7: Run the Takas Scrapy Spider
    run_takas_spider = BashOperator(
        task_id='run_takas_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl takas',
    )

    # Task 8: Run the Simplytek Scrapy Spider
    run_simplytek_spider = BashOperator(
        task_id='run_simplytek_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl simplytek',
    )

    # Task 9: Run the Singer Scrapy Spider
    run_singer_spider = BashOperator(
        task_id='run_singer_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl singer',
    )

    # Task 10: Run the Wasi Scrapy Spider
    run_wasi_spider = BashOperator(
        task_id='run_wasi_spider',
        bash_command='cd /opt/app/scraper && scrapy crawl wasi',
    )

    # Task 11: Run the Transformer script
    run_data_transformer = BashOperator(
        task_id='run_data_transformer',
        bash_command='cd /opt/app/transformer && python sync.py',
    )

    # Define execution order
    run_nanotek >> run_tecroot_spider >> run_mydealz_spider >> run_mysoftlogic_spider >> run_simplytek_spider >> run_wasi_spider >> run_data_transformer
    run_bigdeals_spider >> run_redline_spider >> run_takas_spider >> run_singer_spider >> run_data_transformer

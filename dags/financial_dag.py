import datetime
import math
import json
import logging
import pendulum
import requests
import airflow.macros
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.decorators import dag, task

@task(execution_timeout=datetime.timedelta(minutes=3))
def download_yfinance_data(ds=None):
    """Downloads Adjusted Close data from S&P 500 companies"""

    tickers = ['NVDA','AAPL','META','GOOGL','ABNB','TSLA','AMZN']
    data = yf.download(tickers, start=ds)['Adj Close']
    return data.to_json()

@task(execution_timeout=datetime.timedelta(minutes=3))
def prepare_data(string_data):
    """Creates a list of dictionaries with clean data values"""

    # transforming to dataframe for easier manipulation
    df = pd.DataFrame.from_dict(json.loads(string_data), orient='index')

    values_dict = []
    for col, closing_date in enumerate(df.columns):
        for row, ticker in enumerate(df.index):
            adj_close = df.iloc[row, col]

            if not(adj_close is None or math.isnan(adj_close)):
                values_dict.append(
                    {'closing_date': closing_date, 'ticker': ticker, 'adj_close': adj_close}
                )
            else:
                logging.info("Skipping %s for %s, invalid adj_close (%s)",
                             ticker, closing_date, adj_close)

    return values_dict

# def import_data(prepared_data):
#     """Runs insert statement for each value of prepared data"""
    
#     return PostgresOperator.partial(
#         task_id="insert_data_task",
#         postgres_conn_id="cratedb_connection",
#         sql="""
#         INSERT INTO sp500 (closing_date, ticker, adj_close)
#         VALUES (%(closing_date)s, %(ticker)s, %(adj_close)s)
#         ON CONFLICT (closing_date, ticker) DO UPDATE SET adj_close = EXCLUDED.adj_close;
#         """,
        
#     ).expand(parameters=prepared_data)
    
@dag(
    start_date=pendulum.datetime(2022, 1, 10, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["finance"],
)
    
def financial_data_import():
    yfinance_data = download_yfinance_data()

    prepared_data = prepare_data(yfinance_data)

    PostgresOperator.partial(
        task_id="insert_data_task",
        postgres_conn_id="cratedb_connection",
        sql="""
            INSERT INTO doc.sp500 (closing_date, ticker, adjusted_close)
            VALUES (%(closing_date)s, %(ticker)s, %(adj_close)s)
            ON CONFLICT (closing_date, ticker) DO UPDATE SET adjusted_close = excluded.adjusted_close
            """,
    ).expand(parameters=prepared_data)
    
financial_data_import()
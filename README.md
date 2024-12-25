# Stock Price ETL Pipeline with Astronomer Airflow

## Overview
This project demonstrates a simple **ETL** (Extract, Transform, Load) pipeline using **Astronomer Airflow**, a managed service for Apache Airflow.

## Requirements
- **Astronomer Airflow**: Managed Airflow platform to easily deploy and manage Airflow environments.
- **yfinance**: To fetch stock price data from Yahoo Finance.
- **pandas**: For transforming the fetched stock price data.
- **CrateDB**: A distributed SQL database to load the transformed data.

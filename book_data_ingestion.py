from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import requests
import os
import json
import time
import psycopg2
import logging
import pandas as pd

# Load API keys and database credentials from environment variables
NYT_API_KEY = "8bN9gIv46rlmzaXXM00EJfOzwf6XxVQe"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")  # Use service name from Docker Compose
DB_NAME = os.getenv("POSTGRES_DB", "books_db")
DB_USER = os.getenv("POSTGRES_USER", "airflow")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")

# API Endpoints
NYT_URL = f"https://api.nytimes.com/svc/books/v3/lists/current/hardcover-fiction.json?api-key={NYT_API_KEY}"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}&key=" + GOOGLE_API_KEY
OPEN_LIBRARY_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:{}&format=json&jscmd=data"

# Database Connection Function
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Fetch NYT Bestsellers
def fetch_nytimes_books(**kwargs):
    response = requests.get(NYT_URL)
    if response.status_code == 200:
        data = response.json()
        books = data.get("results", {}).get("books", [])
        isbns = [book["primary_isbn13"] for book in books if "primary_isbn13" in book]
        kwargs['ti'].xcom_push(key='isbns', value=isbns)
        kwargs['ti'].xcom_push(key='nyt_books', value=books)
    else:
        raise Exception(f"NYT API request failed: {response.status_code}")

# Fetch Open Library Data
def fetch_openlibrary_data(**kwargs):
    ti = kwargs['ti']
    isbns = ti.xcom_pull(task_ids='fetch_nytimes_books', key='isbns')
    if not isbns:
        return
    book_metadata = {}
    for isbn in isbns:
        response = requests.get(OPEN_LIBRARY_URL.format(isbn))
        if response.status_code == 200:
            book_metadata[isbn] = response.json()
        time.sleep(1)
    ti.xcom_push(key='openlibrary_data', value=book_metadata)

# Fetch Google Books Data
def fetch_google_books_data(**kwargs):
    ti = kwargs['ti']
    isbns = ti.xcom_pull(task_ids='fetch_nytimes_books', key='isbns')
    if not isbns:
        return
    book_details = {}
    for isbn in isbns:
        response = requests.get(GOOGLE_BOOKS_URL.format(isbn))
        if response.status_code == 200:
            book_details[isbn] = response.json()
        time.sleep(1)
    ti.xcom_push(key='google_books_data', value=book_details)

# Data Quality Checks
def data_quality_checks():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    if df.empty:
        raise Exception("No data found in books table!")
    if df['isbn'].isnull().sum() > 0:
        raise Exception("Missing ISBNs detected!")
    logging.info(f"Data Quality Check Passed: {df.shape[0]} records found.")

# Generate Data Quality Report
def generate_data_quality_report():
    report_dir = "/opt/airflow/reports"
    os.makedirs(report_dir, exist_ok=True)  # Ensure the directory exists

    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    
    report_path = os.path.join(report_dir, "data_quality_report.json")
    report = df.describe().to_json()
    
    with open(report_path, "w") as f:
        f.write(report)

    logging.info(f"Data Quality Report saved at {report_path}")

# DAG Configuration
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 25),
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'book_data_pipeline',
    default_args=default_args,
    schedule_interval='0 9 * * *',  # Runs daily at 9 AM
    catchup=False,
)

with dag:
    with TaskGroup("fetch_data") as fetch_data:
        fetch_nytimes_books = PythonOperator(task_id='fetch_nytimes_books', python_callable=fetch_nytimes_books)
        fetch_openlibrary_data = PythonOperator(task_id='fetch_openlibrary_data', python_callable=fetch_openlibrary_data)
        fetch_google_books_data = PythonOperator(task_id='fetch_google_books_data', python_callable=fetch_google_books_data)

    data_quality_checks = PythonOperator(task_id='data_quality_checks', python_callable=data_quality_checks)
    generate_data_quality_report = PythonOperator(task_id='generate_data_quality_report', python_callable=generate_data_quality_report)

    fetch_data >> data_quality_checks >> generate_data_quality_report

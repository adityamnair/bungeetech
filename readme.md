# Book Data Ingestion Pipeline

## Project Overview
This project implements an ETL (Extract, Transform, Load) pipeline for ingesting book data using Apache Airflow. The pipeline fetches book details from the New York Times API, Google Books API, and Open Library API, processes and validates the data, and loads it into a PostgreSQL database. Additionally, it generates data quality reports and provides a Streamlit dashboard for visualization.

### Architecture Diagram
```
+----------------+     +----------------------+     +--------------------+     +------------------+
|  NYTimes API  | --> |  fetch_nytimes_books  | --> |                    |
+----------------+     +----------------------+     |                    |     +------------------+
                                                |                    | --> | data_quality_checks |
+----------------+     +----------------------+     |  PostgreSQL DB    |     +------------------+
| OpenLibrary API| --> | fetch_openlibrary_data | --> |                    |
+----------------+     +----------------------+     |                    | --> +----------------------+
                                                |                    |     | generate_data_quality |
+----------------+     +----------------------+     |                    |     |      _report         |
| GoogleBooks API| --> | fetch_google_books_data | --> |                    |     +----------------------+
+----------------+     +----------------------+     +--------------------+
```

## Setup Instructions
### Prerequisites
- Docker & Docker Compose installed
- Python 3.8+ (if running locally without Docker)

### Steps to Run the Pipeline
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Create an `.env` file to store API keys (ensure this file is not committed to Git):
   ```bash
   NYTIMES_API_KEY=<your-nyt-api-key>
   GOOGLE_API_KEY=<your-google-api-key>
   POSTGRES_HOST=postgres
   POSTGRES_DB=books_db
   POSTGRES_USER=airflow
   POSTGRES_PASSWORD=airflow
   ```

3. Build and start the services using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```

4. Access the Airflow UI at [http://localhost:8080](http://localhost:8080)
   - Username: `admin`
   - Password: `admin`

5. Trigger the `book_data_pipeline` DAG manually or wait for the scheduled run (daily at 9 AM).

6. Access the Streamlit dashboard at:
   ```bash
   streamlit run app/app.py
   ```
   It will be available at [http://localhost:8501](http://localhost:8501).

## Database Inspection & Sample Queries
Once the data is ingested, you can inspect the database using:
```bash
docker exec -it postgres_container psql -U airflow -d books_db
```

### Sample Queries
- Check total records:
  ```sql
  SELECT COUNT(*) FROM books;
  ```
- Find missing values:
  ```sql
  SELECT * FROM books WHERE isbn IS NULL OR title IS NULL;
  ```
- Identify duplicate records:
  ```sql
  SELECT isbn, COUNT(*) FROM books GROUP BY isbn HAVING COUNT(*) > 1;
  ```
- View data quality report:
  ```bash
  cat /opt/airflow/reports/data_quality_report.json
  ```

## Code Documentation
All Python functions in `book_data_ingestion.py` include docstrings to explain their purpose and usage.

### Key Functions
- `fetch_nytimes_books()`: Fetches bestseller books from NYT API.
- `fetch_openlibrary_data()`: Fetches additional book metadata from Open Library.
- `fetch_google_books_data()`: Retrieves extra book details from Google Books API.
- `data_quality_checks()`: Validates the completeness and integrity of the data.
- `generate_data_quality_report()`: Generates statistical summaries of the ingested data.

## Additional Features
- **Containerization**: The pipeline is fully containerized using Docker.
- **Monitoring & Logging**: Logs are stored in `/opt/airflow/logs` for debugging.
- **Scalability & Maintainability**: The project is modular, with clear separation of concerns.
- **Streamlit Dashboard**: Provides data visualization for book records.

## Authors
- **aditya**


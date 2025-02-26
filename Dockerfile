# Use the official Airflow image
FROM apache/airflow:2.6.3

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow

# Install required Python dependencies
RUN pip install psycopg2-binary pandas requests
# Install required Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
# Create directories for logs and reports
RUN mkdir -p /opt/airflow/logs /opt/airflow/reports

# Set working directory
WORKDIR $AIRFLOW_HOME

# Copy DAGs into the container
COPY dags/ /opt/airflow/dags/

# Copy entrypoint script if needed
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default command to start Airflow
CMD ["/entrypoint.sh"]

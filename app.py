import streamlit as st
import pandas as pd
import psycopg2
import os

# Database credentials
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "books_db")
DB_USER = os.getenv("POSTGRES_USER", "airflow")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")

# Function to fetch data
def get_data():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    query = "SELECT * FROM books;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit App
st.title("📚 Book Data Dashboard")
st.write("Visualizing book data from PostgreSQL.")

df = get_data()
st.dataframe(df)

st.write("### Data Summary")
st.write(df.describe())

st.write("### Top Authors")
top_authors = df['author'].value_counts().head(10)
st.bar_chart(top_authors)

st.write("### ISBN Distribution")
st.bar_chart(df["isbn"].value_counts())



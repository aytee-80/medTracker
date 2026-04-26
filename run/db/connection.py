import psycopg2
import config

def get_db_connection():
    try:
        conn = psycopg2.connect(config.DATABASE_URL, sslmode="require", connect_timeout=10)
        return conn
    except Exception as e:
        print(f" Failed to connect to the database: {e}")
        return None
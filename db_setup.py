
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

PG_USERNAME = os.getenv("PG_USERNAME")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE_NAME = os.getenv("PG_DATABASE_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
PG_DATABASE_PORT = os.getenv("PG_DATABASE_PORT")

def get_conn():
    return psycopg2.connect(
        dbname=PG_DATABASE_NAME,
        user=PG_USERNAME,
        password=PG_PASSWORD,
        host=CLOUD_SQL_CONNECTION_NAME,
        port=PG_DATABASE_PORT
    )


def create_requests_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS request_counts (
                    ip_address VARCHAR(255) NOT NULL PRIMARY KEY,
                    request_count INT DEFAULT 0
                )
            """)
            conn.commit()


if __name__ == "__main__":
    create_requests_table()

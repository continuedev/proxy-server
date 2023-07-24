
import os
from google.cloud.sql.connector import Connector, IPTypes
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

instance_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
db_user = os.getenv("PG_USERNAME")
db_pass = os.getenv("PG_PASSWORD")
db_name = os.getenv("PG_DATABASE_NAME")
ip_type = IPTypes.PRIVATE if os.getenv("PRIVATE_IP") else IPTypes.PUBLIC

connector = Connector(ip_type)

def creator():
    return connector.connect(
        instance_connection_name,
        "pg8000",
        user=db_user,
        password=db_pass,
        db=db_name,
    )

engine = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=creator,
)

def get_conn():
    return engine.connect()

def create_requests_table():
    with get_conn() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS request_counts (
                ip_address VARCHAR(255) NOT NULL PRIMARY KEY,
                request_count INT DEFAULT 0
            )"""))


if __name__ == "__main__":
    create_requests_table()

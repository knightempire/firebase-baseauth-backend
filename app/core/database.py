import pymysql
from .config import settings

def get_db_conn():
    return pymysql.connect(
        host=settings.CLOUDSQL_HOST,
        user=settings.CLOUDSQL_USER,
        password=settings.CLOUDSQL_PASSWORD,
        database=settings.CLOUDSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

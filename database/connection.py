import pymysql
from config import Config

MYSQL_CONFIG = Config.MYSQL_CONFIG

def get_connection():
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        port=MYSQL_CONFIG["port"],
        cursorclass=pymysql.cursors.DictCursor
    )

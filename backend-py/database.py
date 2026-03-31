import pymysql
from pymysql.cursors import DictCursor

def get_conn():
    return pymysql.connect(
        host="localhost",
        port=8889,
        user="root",
        password="root",
        database="BillBerry",
        charset="utf8mb4",
        cursorclass=DictCursor
    )

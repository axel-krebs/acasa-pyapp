# Provide DB access
import os
from pathlib import Path
from sqlite3 import *

def singleton(cls): # PEP 318
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

class Facade:
    """_summary_
        Encapsulate SQLite3 connection. 
        - Provide query methods
        - Provide update methods
        - Provide schema creation
    """

    def __init__(self, db_file_path: Path):
        self._db_file_path = db_file_path
        # Check if DB is available..
        conn = None
        try:
            conn = connect(self._db_file_path)
        except:
            raise RuntimeError("Database could not be opened!")
        finally:
            if conn is not None:
                conn.close()

    def query_db(self, sql_string):
        conn = connect(self._db_file_path)
        res = None
        with self.DbAccessor(conn) as cur:
            try:
                res = cur.execute(sql_string)
            except:
                res = RuntimeError("SQL error")
        return res

    #@singleton
    class DbAccessor(): # 'wrapper' around sqlite3 connection; to be used with 'with .. as'

        def __init__(self, conn):
            self._conn = conn

        def __del__(self): ## try-except?
            del self._conn

        def __enter__(self):
            return self._conn.cursor()

        def __exit__(self, type, value, traceback):
            self._conn.commit()

def create_proxy(db_path: Path):
    return Facade(db_path)

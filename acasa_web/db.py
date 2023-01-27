# Provide DB access for SQLite3 embedded database.
from pathlib import Path
import sqlite3 

def singleton(cls): # PEP 318
    instances = {}
    def getinstance(file_path):
        if cls not in instances:
            instances[cls] = cls(file_path)
        return instances[cls]
    return getinstance

# Use enum instead? TODO
#from enum import Enum
class SQLCode():
    """_summary_
    Return object from execute stmt in SQL.
    """
    
    def __init__(self, error):
        self._err_object = error

    # Provide a 'to_string' method for error object
    def __str__(self) -> str:
        msg = ""
        if isinstance(self._err_object, sqlite3.DatabaseError):
            msg = self._err_object.__str__()
        else: # assume err is string
            msg = self._err_object
        return msg

@singleton
class DbInstance:
    """_summary_
        Encapsulate SQLite3 connection. 
        - Provide query methods
        - Provide update methods
        - Bulk operations
        - etc.
    """

    def __init__(self, db_file_path: Path):
        self._db_file_path = db_file_path
        # Check if DB is available..
        conn = None
        try:
            conn = sqlite3.connect(self._db_file_path)
        except:
            raise RuntimeError("Database could not be opened!")
        finally:
            if conn is not None:
                conn.close()

    # Execute raw SQL string; client responsibility for correctness!
    def execute_sql(self, raw_sql: str) -> SQLCode:
        conn = sqlite3.connect(self._db_file_path)
        with self._DbAccessor(conn) as cur:
            try: 
                cur.execute(raw_sql)
                return SQLCode("SUCCESS")
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)

    # Execute multiple statements and commit after last one or rollback.
    def execute_bulk(self, statements: list) -> SQLCode:
        pass

    def query_db(self, sql_query) -> list:
        conn = sqlite3.connect(self._db_file_path)
        res = None
        with self._DbAccessor(conn) as cur:
            try:
                res = cur.execute(sql_query)
            except sqlite3.DatabaseError as ex:
                res = ex
        return res

    def query_by_example(self, example) -> list:
        pass

    class _DbAccessor(): 
        """
        'Wrapper' around sqlite3 connection; to be used with 'with .. as'
        - mimic transactional behaviour
        """

        def __init__(self, conn):
            self._conn = conn

        def __del__(self): ## try-except?
            del self._conn

        def __enter__(self):
            self._cursor = self._conn.cursor()
            return self._cursor

        def __exit__(self, type, value, traceback):
            self._cursor.close()
            self._conn.commit()


# utility
def create_proxy(db_path: Path):
    return DbInstance(db_path) # creates new instance; however marked singleton..

# Provide DB access
from pathlib import Path
import sqlite3 

def singleton(cls): # PEP 318
    instances = {}
    def getinstance(file_path):
        if cls not in instances:
            instances[cls] = cls(file_path)
        return instances[cls]
    return getinstance

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
    def execute_sql(self, raw_sql: str) -> None:
        conn = sqlite3.connect(self._db_file_path)
        with self._DbAccessor(conn) as cur:
            try: 
                res = cur.execute(raw_sql)
            except sqlite3.DatabaseError as sql_ex:
                res = sql_ex
            return res
        return res

    # Execute multiple statements and commit after last one or rollback.
    def execute_bulk(self, statements: list) -> int:
        pass

    def query_db(self, table, attrs, where_clause) -> list:
        conn = sqlite3.connect(self._db_file_path)
        res = None
        sql_string = "" # TODO
        with self._DbAccessor(conn) as cur:
            try:
                res = cur.execute(sql_string)
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

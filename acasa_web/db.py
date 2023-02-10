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
# from enum import Enum
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
        Encapsulate SQLite3 connections. 
        - Provide query methods
        - Provide update methods
        - Bulk operations
        - etc.
        TODO: implement connection pool, transactions, caching
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
                conn = None

    # Execute raw SQL string; client responsibility for correctness!
    def execute_sql(self, raw_sql: str) -> SQLCode:
        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try: 
                cur.execute(raw_sql)
                return SQLCode("SUCCESS")
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)
    
    # 'Facade' method: Creates SQL 'INSERT .. ON CONFLICT (..) DO UPDATE"
    def upsert(self, table: str, data_set: dict, key_field: str = "ID") -> SQLCode:
        keys = []
        values = []
        for attr_key in data_set: # remember keys and values sperately for later
            keys.append(str(attr_key).lower())
            values.append(data_set[attr_key]) 
        sql = "INSERT INTO " + table + "("
        sql += ",".join(keys)
        sql += ") VALUES("
        sql += ",".join(values)
        sql += ") ON CONFLICT (id) DO UPDATE SET "
        cnt = 0 # needed for comma!
        while cnt < len(keys):
            cur_key = keys[cnt]
            if str(cur_key) != key_field: # omit "id" field for UPSERT, s. function parameter
                sql += " " + str(cur_key).lower() + "=" + "excluded." + str(cur_key).lower()
                if cnt < len(keys) - 1:
                    sql += ","
            cnt += 1
        sql += ";"
        return self.execute_sql(sql)

    # Similar to 'execute', the client is responsible for proper SQL!
    # Invoke 'fetchall' on result from cursor and return rows.
    def query(self, sql_query) -> list:
        conn = sqlite3.connect(self._db_file_path)
        res = None
        with self._TransactionalDbAccessor(conn) as cur:
            try:
                _temp_res = cur.execute(sql_query)
                res = _temp_res.fetchall()
            except sqlite3.DatabaseError as ex:
                res = ex
        return res

    def query_by_example(self, example) -> list:
        pass

    class _TransactionalDbAccessor(): 
        """
        'Wrapper' around sqlite3 connection; to be used with 'with .. as'
        - mimic transactional behaviour: always committed at the end!
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
    return DbInstance(db_path) # creates new SQLite3 instance; however marked singleton..

# Provide DB access for SQLite3 embedded database.
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3 
from util import *

class SQLCode():
    """_summary_
    Return object from execute stmt in SQL.
    """
    
    def __init__(self, msg):
        self._err_object = msg

    # Provide a 'to_string' method for error object (logging!)
    def __str__(self) -> str:
        msg = ""
        if isinstance(self._err_object, sqlite3.DatabaseError):
            msg = self._err_object.__str__()
        else: # assume err is string
            msg = self._err_object
        return msg

class SQLCodes():
    ERROR = SQLCode("General Error!")
    SUCCESS = SQLCode("Success!!")
    WARN = SQLCode("General Warning!")

class Column(Enum):
    INTEGER = int
    VARCHAR = str

# Python Data Object. Comp. JDO: "Entity"; 
class PersistenceCapable(object):
    """Such annotated classes can be persisted to the database table provided as entity name.
    """
    def __init__(self, table_name): # Evaluate decorator arguments
        self._table_name = table_name
        self._persistence_status = 0 # ?

    def __call__(self, cls): # decorated class instantiation
        print('__call__', cls)
        # TODO "enhance" cls, th.i inspect attributes
        return cls

class PersistenceManager: # Draft
    """Obtain a manager for PersistenceCapable objects
    """
    def __init__(self, db_instance):
        self._db_manager = db_instance

    def persist(self, pc: PersistenceCapable):
        pass



# Minimal SQL mapper; only temporary usage! TBR by "PersistenceCapable", s.a. 
class DataObject():
    def __init__(self, entitiy_name, col_values: dict) -> None:
        self._entity_name = entitiy_name
        self._attributes = col_values
    
    def generate_insert(self):
        _res_sql = "INSERT INTO {} (".format(self._entity_name)
        _res_sql += ",".join(self._attributes.keys())
        _res_sql += ") VALUES ("
        _res_sql += ",".join(['\'{}\''.format(val) for val in self._attributes.values()]) # simple string conversion
        _res_sql += ");"
        return _res_sql
    
    def generate_update(self):
        pass

    def generate_delete(self):
        pass
@singleton
class DbInstance():
    """
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
                del conn

    # Execute raw SQL string; client responsibility for correctness!
    def _execute_sql(self, raw_sql: str) -> SQLCode:
        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try: 
                cur.execute(raw_sql)
                return SQLCodes.SUCCESS
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)
    
    def insert(self,data_object: DataObject):
        conn = sqlite3.connect(self._db_file_path)
        gen_sql = data_object.generate_insert()
        with self._TransactionalDbAccessor(conn) as cur:
            try: 
                res = cur.execute(gen_sql)
                return cur.lastrowid
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
        sql += ") VALUES ("
        sql += ",".join(values)
        sql += ") ON CONFLICT (id) DO UPDATE SET " # TODO: what if data_set was empty??
        cnt = 0 # needed for comma!
        while cnt < len(keys):
            cur_key = keys[cnt]
            if str(cur_key) != key_field: # omit "id" field for UPSERT, s. function parameter
                sql += " " + str(cur_key).lower() + "=" + "excluded." + str(cur_key).lower()
                if cnt < len(keys) - 1:
                    sql += ","
            cnt += 1
        sql += ";"
        return self._execute_sql(sql)

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
        - Not a singleton - after all, we have control of this 'inner class'!
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

if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import' fom another program.")
    # raise error?
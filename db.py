# Provide DB access for SQLite3 embedded database.
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from inspect import *
import sqlite3
import sys
from typing import Any
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
        else:  # assume err is string
            msg = self._err_object
        return msg


class SQLCodes():
    ERROR = SQLCode("General Error!")
    SUCCESS = SQLCode("Success!!")
    WARN = SQLCode("General Warning!")


# At a first shot, these are SQLite data types ONLY..
class ColumnTypes(Enum):
    INTEGER = int
    REAL = float
    TEXT = str
    BLOB = object
    NULL = None


class ImproperUsageException(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidConfigurationWarning(Warning):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


pcc_registry = dict()  # persistence capable class registry
# Work-around: During import, instantiation of PersistenceCapable and Column is detached
_class_parsing_tray = {}

# "Python Data Object", comp. JDO: "PersistenceCapable"; necessary b. Entity does not provide a mapping to a the name of
# a table in the database.


class PersistenceCapable():
    """Such annotated classes can be persisted to a database table.
    """

    def __init__(self, table_name: str = None):  # Evaluate decorator arguments
        if table_name is None:
            _class_parsing_tray['table_name'] = False
        else:
            _class_parsing_tray['table_name'] = table_name
        _class_parsing_tray['table_columns'] = []

    def __call__(self, cls):  # decorated class instantiation (import time); attention: called last in the import chain!
        # Therefore, only checks should be made here that everything went right during registration and the class then
        # added to the pcc_registry
        print('__call__', cls)
        if isfunction(cls):
            raise ImproperUsageException(
                "PersistenceCapable must be applied to a class, not a function.")
        elif isclass(cls):
            mbrs = getmembers(cls)
            print("Members: ", mbrs)
        # Check _class_parsing_tray; att. __call__ is invoked at import time as well as runtime, e.g. object creation
        global _class_parsing_tray
        if len(_class_parsing_tray) != 0:
            if not _class_parsing_tray['table_columns']:
                raise InvalidConfigurationWarning(
                    "No columns have been found in the data class.")
            pcc_registry[self] = _class_parsing_tray.copy()
            # When this 'constructor' of the class is called, the members (if any) must have been registered already!
            _class_parsing_tray = {}  # reset
        return self


def infer_sqltype_from_python(t: type = None):
    if t is None:
        raise InvalidConfigurationWarning(
            "Tried to infer SQL type from Python return value, but None given.")
    # match stmt not feasible in Python 3.9!
    elif t == str:
        return ColumnTypes.TEXT
    elif t == int:
        return ColumnTypes.INTEGER
    elif t == float:
        return ColumnTypes.REAL
    elif t == object:
        return ColumnTypes.BLOB
    else:
        return ColumnTypes.NULL # ?

def Column(col_name: str = None, sql_type: ColumnTypes = None):
    def _deco(self):  # self is class method? Check!
        if not isfunction(self):
            raise ImproperUsageException("""A Column decorator must be annotated within a class method, e.g.\n\
                                         \"@Column(col_name=\"id\", sql_type=ColumnTypes.INTEGER) def xyz(self): etc.\"
                                         """)

        # Checking that this def belongs to surrounding class etc.
        func_name = self.__name__

        # name before dot must be class; if defined in standalone function,
        class_name = self.__qualname__.split('.')[0]

        # class_name is the same as func_name, which will be checked below.
        mod_name = self.__module__  # could be empty if @Column used in main!
        if func_name == class_name:
            raise ImproperUsageException(
                "@Column can only be added to class methods!")

        # Because PersistenceCapable does not know about the class, this must be done on occurrence of first @Column tag
        fqdn = mod_name + "." + class_name
        if 'fq_class_name' not in _class_parsing_tray:
            _class_parsing_tray["fq_class_name"] = fqdn
        else:
            if _class_parsing_tray["fq_class_name"] != fqdn:
                raise RuntimeError(
                    "To-be-registered member did not belong to the same class (parsing).")

        # If PersistenceCapable could not find table_name parameter, the name of the class is supposed to be the table
        if _class_parsing_tray["table_name"] is False:
            _class_parsing_tray['table_name'] = class_name

        # Everything ok with class and function, now check decorator args: If not given, try to infer from function name
        # resp. return value annotation.
        nonlocal col_name, sql_type
        if col_name is None:
            col_name = func_name
        if sql_type is None:
            try:
                ret_val = self.__annotations__['return']
                sql_type = infer_sqltype_from_python(
                    ret_val)  # raises exception
            except Exception as ex:
                raise InvalidConfigurationWarning("@Column decorator has no sql_type specified, and none return \
                                                  annotation given.", ex)
        _class_parsing_tray['table_columns'].append(
            {"col_name": col_name, "sql_type": sql_type, "class_method": func_name})

    return _deco


class Query:
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
        # simple string conversion
        _res_sql += ",".join(['\'{}\''.format(val)
                             for val in self._attributes.values()])
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

    def insert(self, data_object: DataObject):
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
        for attr_key in data_set:  # remember keys and values sperately for later
            keys.append(str(attr_key).lower())
            values.append(data_set[attr_key])
        sql = "INSERT INTO " + table + "("
        sql += ",".join(keys)
        sql += ") VALUES ("
        sql += ",".join(values)
        # TODO: what if data_set was empty??
        sql += ") ON CONFLICT (id) DO UPDATE SET "
        cnt = 0  # needed for comma!
        while cnt < len(keys):
            cur_key = keys[cnt]
            if str(cur_key) != key_field:  # omit "id" field for UPSERT, s. function parameter
                sql += " " + str(cur_key).lower() + "=" + \
                    "excluded." + str(cur_key).lower()
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

        def __del__(self):  # try-except?
            del self._conn

        def __enter__(self):
            self._cursor = self._conn.cursor()
            return self._cursor

        def __exit__(self, type, value, traceback):
            self._cursor.close()
            self._conn.commit()


class PersistenceManager:  # Draft
    """Obtain a manager for PersistenceCapable objects
    """

    def __init__(self, db_instance: DbInstance):
        self._db_manager = db_instance

    def persist(self, pc: PersistenceCapable):
        pass

# utility


def create_proxy(db_path: Path):
    # creates new SQLite3 instance; however marked singleton..
    return DbInstance(db_path)


if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import' fom another program.")
    # raise error?

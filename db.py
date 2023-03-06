# Provide DB access for SQLite3 embedded database.
from abc import *
from enum import Enum
from pathlib import Path
from inspect import *
import sqlite3
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


class ColumnTypes(Enum):  # At a first shot, these are SQLite data types ONLY..
    INTEGER = int
    REAL = float
    TEXT = str
    BLOB = object
    NULL = None


class ImproperUsageException(RuntimeError):
    """Raised when a decorator is applied to the wrong type, e.g. a @PersistenceCapable to a function (instead of a 
    class) or a @Column to a class instead of a function.

    Args:
        RuntimeError (_type_): _description_
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidConfigurationWarning(Warning):
    """Raised when an invalid configuration is detected, e.g. a @PersistenceCapable class without columns.

    Args:
        Warning (_type_): _description_
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


# The registry;
# Format: {
#   "class_fqdn": module.Class,
#   "class_members": [
#       {
#           "column_name": name,
#           "column_type": sql_type,
#           "default_value": value,
#           "py_func": name_of_the_original_function
#       }
#   ]
# }
pcc_registry = dict()  # persistence capable class registry; naming resp. QL for querying

# Work-around: During import, instantiation of PersistenceCapable and Column is detached; this "tray" serves for sharing
_class_parsing_tray = {}

# "Python Data Object", comp. JDO: "PersistenceCapable"; necessary b. Entity does not provide a mapping to a the name of
# a table in the database.


class _PersistenceCapable():

    @abstractmethod
    def save():
        raise "Should never be invoked directly (abstract)!"

    @abstractmethod
    def delete():
        raise "Should never be invoked directly (abstract)!"


def save(obj):
    """Method attached to persistent objects. Make sure, a entity manager instance is available, wehn invoking this fct.

    Args:
        obj (_type_): Implicit instance
    """
    print("Saving object..")


def delete(obj):
    """Method attached to persistent objects. Make sure, a entity manager instance is available, wehn invoking this fct.

    Args:
        obj (_type_): Implicit instance
    """
    print("Deleting object..")

# Property descriptor for persistent attributes


class _GetterSetter():
    def __init__(self, value: Any = None) -> None:
        self._v = value

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self
        return self._v

    def __set__(self, instance, value) -> None:
        self._v = value


class PersistenceCapable(_PersistenceCapable):
    """Use as decorator. Such decorated classes can be persisted to a database table, s. attached methods (class or 
       instance).
    """

    # Evaluate decorator arguments; self = PersistenceCapable; attention: since __call__ on ctor returns the mixin; this
    # will be also invoked when an object of the original class is created!
    def __init__(self, *ctor_args, **kwargs):
        # super().__init__(**kwargs)
        if ctor_args:
            print("Don't know what to do with nameless parameters..")
        elif kwargs:  # invoked on import-time by decorator; noly possible parameter is "table_name":
            table_name = kwargs["table_name"]
            if table_name:
                _class_parsing_tray['table_name'] = table_name
                _class_parsing_tray['table_columns'] = []
            else:
                print("TODO: set named parameters as attributes")

    # Decorated class instantiation (import time); Attention: called last after Column, Join etc. have been called..
    # Therefore, only checks should be made here that everything went right during registration and decorated members
    # have been registered orderly.
    def __call__(self, *args):

        if args is None or len(args) == 0:
            raise ImproperUsageException(
                "Constructor with no-args invoked - this should not happen.")

        else:
            first_arg = args[0]
            if isfunction(first_arg):
                raise ImproperUsageException(
                    "Decorator @PersistenceCapable must be applied to a class, not a function!")

            # Handle import-time construction
            elif isclass(first_arg):
                clz = first_arg
                clz_name = clz.__qualname__
                clz_mod_name = clz.__module__
                clz_qname = clz_mod_name + "." + clz_name
                clz_props = {}

                # Check _class_parsing_tray; __call__() is invoked at "import time",
                global _class_parsing_tray
                if len(_class_parsing_tray) != 0:  # Initialization phase (import time)

                    # No @Column functions detected
                    if not _class_parsing_tray['table_columns']:
                        raise InvalidConfigurationWarning(
                            "No @Column definitions found in the persistent class!")

                    # Extend the given class with I/F methods
                    clz_base = clz.__base__
                    # No, assume NO ONHERITANCE for PersistenceCapable; maybe later..
                    clz_base_name = clz_base.__name__

                    # Extend type with THIS as a mixin
                    try:
                        clz = type(clz_name, (PersistenceCapable,
                                              clz_base), dict(clz.__dict__))
                    except TypeError as typEx:
                        raise ImproperUsageException(
                            "PersistenceCapable-decorated classes may not inherit (s. Release)")

                    setattr(clz, "save", save)
                    setattr(clz, "delete", delete)

                    for col_def in _class_parsing_tray["table_columns"]:
                        setattr(clz, col_def["class_prop"], _GetterSetter(
                            col_def["default_value"]))

                    # Register parsing results
                    pcc_registry[clz_qname] = clz_props

                    #  Reset the tray for next class, if any
                    _class_parsing_tray = {}  # reset

                    return clz

                else:
                    raise "Class-parsing error at import time: tray was empty."

            else:
                raise ImproperUsageException(
                    "@PersistenceCapable must be used with a class.")

        return self  # should not happen! Raise exception?

    @classmethod
    def load(clz, key):
        print("Class Loading..", key)
        return PersistenceCapable.__new__(clz)

    @classmethod
    def findAll(clz) -> list:
        print("Loading all..")

    @classmethod
    def find(clz, filter):
        print("Filtered loading..")


def _infer_sqltype_from_python(t: type = None):
    if t is None:
        raise InvalidConfigurationWarning(
            "Tried to infer SQL type from Python return value, but None type given.")
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
        return ColumnTypes.NULL  # ?


def Column(col_name: str = None, sql_type: ColumnTypes = None):
    """Define a persistent field. Comp. to standard @property decorator.

    Args:
        col_name (str, optional): _description_. Defaults to None.
        sql_type (ColumnTypes, optional): _description_. Defaults to None.
    """

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

        self_sig = signature(self)
        self_src = getsource(self)
        self_value = self()  # simplest way to inspect the return value of this function!
        # Because PersistenceCapable does not know about the class, this must be done on occurrence of first @Column tag
        fqdn = mod_name + "." + class_name
        if 'fq_class_name' not in _class_parsing_tray:
            _class_parsing_tray["fq_class_name"] = fqdn
        else:
            if _class_parsing_tray["fq_class_name"] != fqdn:
                raise RuntimeError(
                    "To-be-registered member did not belong to the same class (parsing).")

        # If PersistenceCapable could not find table_name parameter, the name of the class is supposed to be the table
        if "table_name" in _class_parsing_tray:
            _class_parsing_tray['table_name'] = class_name

        # Everything ok with class and function, now check decorator args: If not given, try to infer from function name
        # resp. return value annotation.
        nonlocal col_name, sql_type
        if col_name is None:
            col_name = func_name  # name of function will be name of column
        if sql_type is None:
            try:
                ret_val = self.__annotations__[
                    'return']  # maybe empty -> exception
                sql_type = _infer_sqltype_from_python(
                    ret_val)  # raises exception
            except Exception as ex:
                raise InvalidConfigurationWarning("@Column decorator has no sql_type specified, and none return \
                                                  annotation given.", ex)

        _class_parsing_tray['table_columns'].append(
            {"class_prop": func_name, "column_name": col_name, "column_type": sql_type, "default_value": self_value})

    return _deco


class JoinType(Enum):
    LEFT = "left",
    RIGHT = "right"


def Join(join_type: JoinType):
    pass


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

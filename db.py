# Provide DB access for SQLite3 embedded database.
from abc import *
from collections import namedtuple
from enum import Enum
from pathlib import Path
from inspect import *
import sqlite3
from typing import Any
import unittest


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
    SUCCESS = SQLCode("Success!")
    WARN = SQLCode("General Warning!")


class ColumnTypes(Enum):  # At a first shot, these are SQLite data types ONLY..
    INTEGER = int
    REAL = float
    TEXT = str
    BLOB = object
    UNKNOWN = None


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


class InvalidMappingException(Exception):
    """Raised whenever a invalid constellation in the mapping data is found, e.g. missing primary key etc. 

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class DbAccessException(RuntimeError):
    """Raised if DB is not available, either Path not found or remote connection problem. 

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class TypeCastError(TypeError):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MissingImplementationError(TypeError):
    """Raised by the abstract superclass when a property is not overwritten. 

    Args:
        TypeError (_type_): Handled as TypeError, though actually "ImplementationError", which does not exist. 
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


# miniimal class to hold column name & value
_ColumnValue = namedtuple('_ColumnValue', ['col_name', 'col_value'])


# Attentiona: 'a_dict' has to be a flat map!
def extract_key_columns(a_dict: dict, keys_list: list):
    normal_cols = []
    key_cols = []
    for col_key in a_dict:
        cv = _ColumnValue(col_key, a_dict[col_key])
        if col_key in keys_list:
            key_cols.append(cv)
        else:
            normal_cols.append(cv)
    return normal_cols, key_cols  # Mutable!

# Design: This 'dataobject' could as well have been coded into the PersistenceCapable class; however, thus I introduced
# an indirection that 'maps' the class object to 'lower' data structures and succinctly decouples the object model from
# the SQL implementation.


class DataObject():
    """DataObject encapsulates the values given in the ctor and offers methods to generate SQL from these; it shall be
    treated as a 'immutable' data structure. 
    Args: 
        - entitiy_name: The name of the table in the database
        - col_values: A simple key->value map (dict)
        - primary_keys: A list of columns that shall be treated as primary key.
    Raises:
        InvalidMappingException: Parameter for ctor are not valid (several causes)
            """

    def __init__(self, entity_name=None, col_values: dict = None, primary_keys: list = None) -> None:
        if not entity_name:
            raise InvalidMappingException("Name for a table must be given.")
        if not col_values:
            raise InvalidMappingException("No columns defined.")
        if not primary_keys:
            raise InvalidMappingException(
                "DataObjects must have at least one primary key defined.")

        # distinguish between "normal" attributes and primary keys
        columns, key_columns = extract_key_columns(col_values, primary_keys)

        self._entity_name = entity_name
        self._columns = columns
        self._primary_keys = key_columns

    def table_name(self):
        return self._entity_name

    def key_columns(self):
        """'Public' getter for the key columns property. 

        Returns:
            _type_: A list of _ColumnValue objects, s. def. 
        """
        return self._primary_keys

    # The reverse of whats been done in ctor with 'col_values'
    def merge_columns(self) -> dict:
        merged = self._columns + self._primary_keys
        return dict(merged)

    def as_paired_lists(self):  # convenience method for SQL generation
        column_names = []
        column_values = []
        all_attributes = [*self._columns, *self._primary_keys]
        for col_name, col_value in all_attributes:
            column_names.append(col_name)
            column_values.append(col_value)
        return column_names, column_values

    def update_pk(self, new_keys: dict = None):
        for key_col in self._primary_keys:
            current_colname = key_col[0]
            if current_colname in new_keys:
                key_col = _ColumnValue(
                    current_colname, new_keys[current_colname])

# @singleton


class _ObjectStore(ABC):

    @abstractmethod
    def create(self, data_object: DataObject):
        raise MissingImplementationError(
            "Implementation of _ObjectStore ist missing required override: def create()")

    @abstractmethod
    def read(self, data_object: DataObject):
        raise MissingImplementationError(
            "Implementation of _ObjectStore ist missing required override: def read()")

    @abstractmethod
    def update(self, data_object: DataObject):
        raise MissingImplementationError(
            "Implementation of _ObjectStore ist missing required override: def update()")

    @abstractmethod
    def delete(self, data_object: DataObject):
        raise MissingImplementationError(
            "Implementation of _ObjectStore ist missing required override: def delete()")


class SQLiteInstance(_ObjectStore):
    """
        Encapsulate SQLite3 "connections" (file). 
        - Provide DML operations (CRUD)
        - Provide query methods
        - QBE (Query By Example)
        - Provide 'raw' SQL execution methods
        - Bulk operations
        - etc.
        TODO: implement connection pool, caching
    """

    def __init__(self, db_file_path: Path):
        self._db_file_path = db_file_path

        # Check if DB is available..
        conn = None
        try:
            conn = sqlite3.connect(self._db_file_path)
        except:
            raise DbAccessException("Database could not be opened!")
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

    def create(self, data_object: DataObject):
        col_name_list, col_value_list = data_object.as_paired_lists()
        _res_sql = "INSERT INTO {} (".format(data_object.table_name())
        _res_sql += ",".join(col_name_list)
        _res_sql += ") VALUES ("
        _res_sql += ",".join(['\'{}\''.format(val)  # simple string conversion
                             for val in col_value_list])
        _res_sql += ");"
        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try:
                cur.execute(_res_sql)
                pk = cur.lastrowid
                pk_dict = {}
                for key_col in data_object.key_columns():
                    pk_dict[key_col] = pk
                data_object.update_pk(pk_dict)
                return data_object
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)

    def read(self, data_object: DataObject):
        col_name_list, col_value_list = data_object.as_paired_lists()
        _res_sql = "SELECT "
        _res_sql += ",".join(col_name_list)
        _res_sql += " FROM {}".format(data_object.table_name())
        _res_sql += " WHERE "
        key_columns = data_object.key_columns()
        _cnt = len(key_columns)
        for col_name, col_value in data_object.key_columns():
            _res_sql += col_name + "=" + col_value
            _cnt -= 1
            if _cnt > 0:
                _res_sql += " AND "

        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try:
                res = cur.execute(_res_sql)
                # TODO set values
                return data_object
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)

    def update(self, data_object: DataObject):
        _res_sql = "UPDATE {}".format(self._entity_name)
        _res_sql += " SET "
        for col_item in self._columns:
            _res_sql += col_item[0] + "=" + col_item[1]
        _res_sql + " WHERE "
        for prim_key in self._primary_keys:
            _res_sql += prim_key + "=" + self._primary_keys[prim_key]
        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try:
                res = cur.execute(_res_sql)
                return cur.lastrowid
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)

    def delete(self, data_object: DataObject):
        _res_sql = "DELETE FROM {}".format(self._entity_name)
        _res_sql += " WHERE "
        conn = sqlite3.connect(self._db_file_path)
        with self._TransactionalDbAccessor(conn) as cur:
            try:
                res = cur.execute(_res_sql)
                return cur.lastrowid
            except sqlite3.DatabaseError as sql_ex:
                return SQLCode(sql_ex)

    # 'Facade' method: Creates SQL 'INSERT .. ON CONFLICT (..) DO UPDATE"
    def upsert(self, table: str, data_set: dict, key_field: str = "ID") -> SQLCode:
        keys = []
        values = []
        for attr_key in data_set:  # remember keys and values seperately for later
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
        'Wrapper' around sqlite3 connection; to be used like 'with _TransactionalDbAccessor(connection) as cursor'
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


class _PersistenceCapable():
    """Interface; do not subclass!
    """

    @abstractmethod
    def save():
        raise "Should never be invoked directly (abstract)!"

    @abstractmethod
    def delete():
        raise "Should never be invoked directly (abstract)!"


class _PersistenceManager(ABC):

    @abstractmethod
    def load(self, key: Any):
        raise "This is the abtract method - programming error!"

    @abstractmethod
    def persist(self, pc: _PersistenceCapable):
        raise "This is the abtract method - programming error!"


def _check_persistence_capable(pc):
    if not isinstance(pc, _PersistenceCapable):
        raise TypeCastError("Submitted class not _PersistenceCapable.")


class RelationalPersistenceManager(_PersistenceManager):
    """Obtain a manager for PersistenceCapable objects
    """

    def __init__(self, db_instance: SQLiteInstance):
        self._db_proxy = db_instance

    # SELECT single
    def load(self, _pc: _PersistenceCapable, keys: list):
        _check_persistence_capable(_pc)
        _do = _data_object(_pc)
        self._db_proxy.read(_do)
        _update_internal(_pc, _do)
        return _pc  # !

    # INSERT/UPDATE
    def persist(self, _pc: _PersistenceCapable):
        _check_persistence_capable(_pc)
        _do = _data_object(_pc)
        res = self._db_proxy.create(_do)
        if isinstance(res, SQLCode):
            print(
                "An error occurred.. Expected DataObject as a return value, got SQLCode: ", res)
        else:
            _update_internal(_pc, _do)
        return _pc  # !

    def delete(self, _pc: _PersistenceCapable):
        _check_persistence_capable(_pc)
        return _pc


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

persistence_manager = None


def set_relational_persistence_manager(db: _ObjectStore) -> RelationalPersistenceManager:
    global persistence_manager
    persistence_manager = RelationalPersistenceManager(db)


def save(obj: _PersistenceCapable):
    """Method attached to persistent objects. Make sure, a entity manager instance is available, wehn invoking this fct.

    Args:
        obj (_type_): Implicit instance
    """
    if persistence_manager is None:
        print("persistence_manager was None, pls. set with set_persistence_manager(db: DbInstance)")
    else:
        persistence_manager.persist(obj)


def delete(obj: _PersistenceCapable):
    """Method attached to persistent objects. Make sure, a entity manager instance is available, when invoking this fct.

    Args:
        obj (_type_): Implicit instance
    """
    if persistence_manager is None:
        print("persistence_manager was None, pls. set with set_persistence_manager(db: DbInstance)")
    else:
        persistence_manager.delete(obj)


def _data_object(pc: _PersistenceCapable) -> DataObject:
    # Sth. between property, GetterSetter etc.. Best description: Converter!
    # Args:
    #    obj (_PersistenceCapable): An object that has this function been attached to.
    # Returns:
    #    _type_: A DataObject type that can easily be persisted.

    table_name = pc._table_name
    col_val_dict = {}
    for colummn_name in pc._value_map:
        col_val_dict[colummn_name] = pc._value_map[colummn_name]["current_value"]
    key_col_names = pc._primary_keys
    return DataObject(table_name, col_val_dict, key_col_names)

# TODO merge with data_object(); pass pc as 'proxy'


def _update_internal(_pc: _PersistenceCapable, _do: DataObject) -> None:

    # Attention: When coming from create, pc gets a new value for the primary key; however, the pc.__primary_keys only
    # contains the _names_ of the primary key columns, so nothing to update there! The keys must correspond, what is not
    # checked at the moment..
    merged = _do.merge_columns()
    for col_key in merged:
        _pc._value_map[col_key] = merged[col_key]


# Property descriptor for persistent attributes
VALUE_MAP_NAME = "_value_map"


class _GetterSetter():  # Attribute descriptor

    # column_name serves as key for the value_map
    def __init__(self, column_name: str = "") -> None:
        self._column_name = column_name

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            print("No instance!")  # Raise exception?
            return self
        else:
            if hasattr(instance, VALUE_MAP_NAME):
                return instance._value_map[self._column_name]["current_value"]
            else:
                print("Instance's _value_map not found.")
                return self

    def __set__(self, instance, value) -> None:
        if instance is None:
            print("No instance!")  # Raise exception?
            return self
        else:
            if hasattr(instance, VALUE_MAP_NAME):
                instance._value_map[self._column_name]["current_value"] = value
            else:
                print("Instance's _value_map not found.")
                return self


class PersistenceCapable(_PersistenceCapable):
    """Use as decorator. Such decorated classes can be persisted to a database table, s. attached methods (class or 
       instance).
    """

    # Evaluate decorator arguments; self = PersistenceCapable; attention: since __call__ on ctor returns the mixin; this
    # will be also invoked when an object of the original class is created!
    def __init__(self, *ctor_args, **kwargs):
        # super().__init__(**kwargs) no.
        if ctor_args:
            print("Don't know what to do with keyless parameters..")

        # invoked on import-time by decorator; only possible parameter is "table_name" (for now)
        elif kwargs:
            if "table_name" in kwargs:
                table_name = kwargs["table_name"]

                # now, somebody may erraneously calls the ctor with 'table_name' parameter again (after parsing)
                self_clz = self.__class__
                if self_clz in pcc_registry.values():
                    raise ImproperUsageException(
                        "Class already registered: You may not use 'table_name' as a keyword in its constructor!")

                _class_parsing_tray['table_name'] = table_name
                _class_parsing_tray['table_columns'] = []
                _class_parsing_tray['table_joins'] = []
            else:
                print("TODO: set named parameters as attributes")
        else:  # Empty ctor on domain object invoked OR table_name not provided! Idle FTTB
            print(
                "Empty ctor on domain object invoked OR table_name not provided! Idle FTTB")

    # Decorated class instantiation (import time); Attention: called last after Column, Join etc. have been called..
    # Therefore, only checks should be made here that everything went right during registration and decorated members
    # have been registered orderly. Ctor invocation of original domain class must not be paid attention to.

    def __call__(self, *args):  # self = PersistenceCapable!

        if args is None or len(args) == 0:
            raise ImproperUsageException(
                "Constructor with no-args invoked - this should not happen.. Is @PersistenceCapable attached to class?")

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

                # Check _class_parsing_tray; __call__() is invoked at "import time",
                global _class_parsing_tray
                if len(_class_parsing_tray) != 0:  # Initialization phase (import time)

                    # No @Column functions detected
                    if not _class_parsing_tray['table_columns']:
                        raise InvalidConfigurationWarning(
                            "No @Column definitions found in the persistent class!")

                    # Extend the given class with I/F methods
                    # should be 'object', otherwise not supported, s. try-except block below
                    clz_base = clz.__base__

                    # No! Assume NO INHERITANCE for PersistenceCapable; maybe later..
                    clz_base_name = clz_base.__name__

                    # Extend type with THIS as a mixin; this could be done prior to eval parsing_tray, however, thus the
                    # operation is omitted if configuration error exist.
                    try:
                        clz = type(clz_name, (PersistenceCapable,
                                              clz_base), dict(clz.__dict__))
                    except TypeError as typEx:
                        raise ImproperUsageException(
                            "PersistenceCapable-decorated classes may not inherit (s. Release)", typEx)

                    # save() and delete() are instance methods: These fcts. get bound to THIS. Actually, these functions
                    # will eval the _value_map and _table_name attributes that have just been set on the instance..
                    setattr(clz, "save", save)
                    setattr(clz, "delete", delete)

                    # initialize columns map and attach getter-setter methods
                    value_map = {}
                    primary_keys = []  # maybe compound!

                    for col_def in _class_parsing_tray["table_columns"]:

                        # Re-mapping for handy-ness
                        col_name = col_def["column_name"]
                        value_map[col_name] = {
                            "column_type": col_def["sql_type"],
                            "default_value": col_def["default_value"],
                            "current_value": col_def["default_value"]
                        }

                        if col_def["primary_key"]:
                            primary_keys.append(col_name)

                        # Provide a "Getter" and "Setter" for the values as instance "properties" (members)
                        setattr(self, col_def["class_prop"],
                                _GetterSetter(col_name))

                    self._table_name = _class_parsing_tray["table_name"]
                    self._value_map = value_map  # attach to instance
                    self._primary_keys = primary_keys

                    # Register parsing results
                    pcc_registry[clz_qname] = clz

                    #  Reset the tray for next class, if any
                    _class_parsing_tray = {}  # reset

                    return clz

                else:
                    raise "Class-parsing error at import time: tray was empty."

            else:
                raise ImproperUsageException(
                    "@PersistenceCapable must be used with a class.")

        return self  # should not happen! Raise exception?

    def __repr__(self) -> str:
        clz = self.__class__.__name__
        str_repr = "PersistenceCapable[{}]".format(clz)
        return str_repr

    def __str__(self) -> str:
        clz = self.__class__.__name__
        str_repr = "PersistenceCapable[{}]".format(clz)
        return str_repr

    @classmethod
    def load(clz, keys) -> _PersistenceCapable:
        # global persistence_manager
        if persistence_manager is None:
            print(
                "persistence_manager was None, pls. set with set_persistence_manager(db: DbInstance)")
            return clz
        else:
            clz_inst = persistence_manager.load(clz, keys=keys)
            return clz_inst

    @classmethod
    def findAll(clz) -> list:
        print("Loading all..")

    @classmethod
    def find(clz, filter) -> list:
        print("Filtered loading..")


def _infer_sqltype_from_python(t: type = None):
    if t is None:
        raise InvalidConfigurationWarning(
            "Tried to infer SQL type from Python return value, but None type given.")
    # match stmt not feasible in Python 3.9!
    elif t is str:
        return ColumnTypes.TEXT
    elif t is int:
        return ColumnTypes.INTEGER
    elif t is float:
        return ColumnTypes.REAL
    elif t is object:
        return ColumnTypes.BLOB
    else:
        return ColumnTypes.UNKNOWN  # ?

# @Column decorator applied to 'fields' (property, which decorates functions), therefore a function wrapper, not class


def Column(col_name: str = None, sql_type: ColumnTypes = None, primary_key: bool = False):
    """Define a persistent field. Comp. to standard @property decorator. 

    Args:
        col_name (str, optional): _description_. Defaults to None.
        sql_type (ColumnTypes, optional): _description_. Defaults to None.
    """

    def _deco(self):  # 'self' must not be a class
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

        # If PersistenceCapable could not find table_name parameter, the name of the class is assumed the table name
        if "table_name" not in _class_parsing_tray:
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
            {
                "class_prop": func_name,
                "column_name": col_name,
                "sql_type": sql_type,
                "default_value": self_value,
                "primary_key": primary_key
            }
        )

    return _deco


class JoinType(Enum):
    LEFT = "left",
    RIGHT = "right"


def Join(join_type: JoinType):
    pass


class Query:
    pass

# utilities


def create_proxy(db_path: Path) -> SQLiteInstance:
    # creates new SQLite3 instance; however marked singleton..
    return SQLiteInstance(db_path)


class UnitTestSQLite(unittest.TestCase):

    def test_PersistentCapable_properties_added(self):
        @PersistenceCapable(table_name="simple_relation")
        class SimpleRelation():

            @Column()
            def id() -> int: return 1

            def fancy(): pass  # must not be 'swallowed'!

        sr = SimpleRelation()
        assert hasattr(sr, 'load')
        assert hasattr(sr, 'save')
        assert hasattr(sr, 'delete')
        assert hasattr(sr, 'find')
        assert hasattr(sr, 'findAll')
        assert hasattr(sr, 'id')
        assert hasattr(sr, 'fancy')

    def test_PersistentWithoutColumn(self):
        with self.assertRaises(Exception) as context:
            @PersistenceCapable(table_name="crash_course")
            class CrashCourse():
                pass  # no columns defined
        self.assertTrue(isinstance(context.exception,
                        InvalidConfigurationWarning))


if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import' fom another program.")
    print("Will run unit test now..")
    unittest.main()

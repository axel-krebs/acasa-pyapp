#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Restaurant ACASA client utilities
from arango import ArangoClient, version as arango_version
import csv
import datetime
import errors as ERR
import os
from pathlib import Path
import uvicorn
import yaml
# modules
import license_management as L_M
import output_management as OUTPUT_MGMT
import order_management as ORDER_MGMT
from acasa_admin.admin_gup import start_admin_app
from db import create_proxy, DataObject

os.chdir(Path(__file__).parent)

SCRIPT_PATH = Path(__name__).parent.resolve()
SQL_PATH = Path("{}{}products_db.sql".format(SCRIPT_PATH, os.sep)) # hard-coded
ACASA_WEB_1_DEPLOYMENT_FOLDER = "acasa_web_1"

# Metadata for CSV-import files: attributes must be in the given list!
# Format: {table_name => [attribute1, attribute2, etc.]}
CONFIG_FILE = Path("{}{}config.yaml".format(SCRIPT_PATH, os.sep))

def show_environment():
    print("Arango: ", arango_version)
    print("CSV: ", csv.__version__)

# load config.yaml 
def load_config() -> dict:
    """ Load the menu from a YAML file.
        TODO: Make this function private to this script.. ;-)
    Raises:
        ERR.LicenseError: ;-)

    Returns:
        dict: The configuration as dict.
    """
    with open(CONFIG_FILE, mode = "r", encoding = "UTF-8") as openfile:
        cfg_text = openfile.read()
        config = yaml.safe_load(cfg_text)
        if not L_M.check_valid(config["license_key"]):
            raise ERR.LicenseError("Your license has probably expired.. :-)")
    return config

# Initialize the database schema. The schema file resides in the current directory and 
# must be splitted into a set of strings that are executed in their own transaction (no bulk).
def create_schema():
    sql_stmts = list()
    with open(SQL_PATH, mode = "r", encoding = "UTF-8") as sql:
        current_str = ""
        comment_line = False
        for line in sql.readlines():
            if line.startswith("**/"):
                comment_line = False
                continue
            elif line.startswith("/**"):
                comment_line = True
            if comment_line: continue
            # single-line comment
            if line.startswith("--"): continue
            # handle commented code
            if line.rfind(";") > 0:
                left_str, right_str = line.split(";")
                sql_stmts.append(current_str + left_str) # no strip, line break is in right string
                current_str = ""
            else:
                current_str += line.strip("\n") # remove Zeilenumbruch    
   
    for sql_stmt in sql_stmts:
        res_code = db_proxy._execute_sql(sql_stmt)
        print("SQL executed: {}, result is: {}".format(sql_stmt, res_code))

# Load product data into SQL database; assume customer has no interface to SQLite3 but Excel (CSV)
def load_csv(file_path: Path, fn: list) -> list:
    ret_list = []
    with open(file_path,mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file, fieldnames=fn, delimiter="|")
        next(csv_reader) # skip headers
        for line in csv_reader:
            ret_list.append(line)
    return ret_list

def start_db_admin(entities):
    while True:
        print("You're in DB admin. Pls. choose from following operations:")
        print("\t0. Quit DB admin.")
        print("\t1. Initialize database (schema creation).")
        print("\t2. Load data from CSV.")
        print("\t3. Enter custom SQL.")
        print("\t4. Create web db (users, translations).")
        # get hold of DB controller (facade)

        user_choice = input("\t>")
        if user_choice == '0':
            break
        elif user_choice == '1':
            create_schema()    
        elif user_choice == '2':
            print("Loading files.. ")
            for entity_name in entities:
                attrs = entities[entity_name]
                csv_file_path = "{}{}{}.csv".format(SCRIPT_PATH.resolve(), os.sep, entity_name)
                res_csv = load_csv(csv_file_path, attrs)

                # convert to SQL string; TODO move this code to a mapping facade object!
                for data_set in res_csv:
                    
                    # send to controller
                    sql_code = db_proxy.upsert(entity_name, data_set, "id")
                    print("SQL returned: ", sql_code)
        elif user_choice == '3':
            custom_sql = input("SQL>")
            res_csv = db_proxy._execute_sql(custom_sql)
            print("SQL executed: {}, result is: {}".format(custom_sql, res_csv))
        elif user_choice == '4':
            create_user_schema(document_store())

config = load_config()
db_name = config['database']['file_name']
db_path = os.path.join(os.path.dirname(__file__), db_name)
db_proxy = create_proxy(db_path)

# User database (Arango) #

def arango_client(timeout: int = 12, max_retries: int = 3) -> ArangoClient:
    arango_url = "http://{}:{}".format(config['arango']['host_name'], config['arango']['host_port']) # closure
    arango_client = ArangoClient(arango_url)
    arango_client.request_timeout = timeout
    return arango_client

def check_database_exists():
    try:
        sys_db = arango_client().db('_system', username='root', password=config["arango"]["root_password"]) # closure
        db_name = config["arango"]["db_name"]
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
    except ConnectionAbortedError as CAE:
        print("Connection not possible! Have you started the server?")
    else:
        return db_name

def document_store():
    user_db_name = check_database_exists()
    if user_db_name == config["arango"]["db_name"]:
        return arango_client().db(user_db_name, 
                                  username=config["arango"]["app_user"], 
                                  password=config["arango"]["app_password"])
    else:
        raise RuntimeError("Couldn't get a handle to the document store!")
    
def create_user_schema(acasa_db): 

    # 'WebUsers' collection
    if acasa_db.has_collection('WebUsers'):
        users = acasa_db.collection('WebUsers')
    else:
        users = acasa_db.create_collection('WebUsers')
        users.add_hash_index(fields=['name'], unique=False)
        users.truncate()
        insert_test_user(users)

    # 'Translations' collection
    if acasa_db.has_collection('Translations'):
        translations = acasa_db.collection('Translations')
    else:
        translations = acasa_db.create_collection('Translations')
    load_translations(translations)
    print("User schema created, tranlsations loaded.")

def insert_test_user(user_coll):
    return user_coll.insert({"Name": "Joe Doe", "Age": 35})

def load_translations(transl_coll):
    pass # TODO Find a way for not-programmers to enter translations easily..

# global cache is shared between dynamic web pages and RESTful web services #
def init_cache(global_cache: dict, db_inst):
    _PROD_SQL = """SELECT p.name AS product_name, 
                p.price AS Product_price, 
                c.name AS category_name 
            FROM products p, categories c 
            WHERE p.category_id = c.id"""
    prods = db_inst.query(_PROD_SQL)
    prods_by_cat = dict()
    for p_name, p_price, p_category in prods:
            if not p_category in prods_by_cat:
                    prods_by_cat[p_category] = list()
            prods_by_cat[p_category].append({"name": p_name, "price": p_price})
    global_cache['prods'] = prods_by_cat # Cache all prods/categories in dict
    global_cache['user_settings'] = {} # hmm...

def create_web_server():
    from web import create_instance, WebStore, ContextCache
    class AcasaWebStore(WebStore): # class on-the-fly.. respect I/F!

        def __init__(self, acasa_db: ArangoClient, needs_initialization: bool):
                self._db = acasa_db

        def is_prepared(self):
                return False # Calls prepare(), s.b.

        def prepare(self):
            create_user_schema(self._db) # s.a.
            return self

        def get_user_for_cookie(self, cookie):
                self._db.aql.execute('FOR doc IN WebUsers RETURN doc')

        def create_user(self, name: str = "", email: str = ""):
                pass
        
    acasa_doc_store = AcasaWebStore(document_store(), True) # inject
    WEB_PATH = Path("{}{}{}".format(SCRIPT_PATH, os.sep, ACASA_WEB_1_DEPLOYMENT_FOLDER))
    ctx_cache = ContextCache()
    init_cache(ctx_cache, db_proxy) # nsn.. inversion of control possible? should be on deployment time..
    web_inst_1 = create_instance(WEB_PATH, acasa_doc_store, ctx_cache)
    return web_inst_1, ctx_cache # Make this function executable by uvicorn for cloud deployment, e.g. Heroku

# Depricated! TODO Introduce integration tests
def start_order_management(config, lang, sql_db):
    class ProductDbMapper():

        def __init__(self, db):
            self._db_facade = db

        def get_products(self):
            _sql = """SELECT 
                        p.id AS product_id,
                        p.name AS product_name,
                        p.price AS product_price,
                        c.name AS category_name 
                    FROM products p, categories c 
                    WHERE p.category_id = c.id
                    """
            prods = self._db_facade.query(_sql)
            prod_by_cat = dict()
            for product_id, product_name, product_price, category_name in prods:
                if not category_name in prod_by_cat:
                    prod_by_cat[category_name] = list()
                prod_by_cat[category_name].append({"id": product_id, "name": product_name, "price": product_price})
            return prod_by_cat  # Automatic JSON converting! :-)
        
    user_id = input("Pls. tell us your ID> ")
    # TODO verify integrity of ID
    order_items = ORDER_MGMT.take_order(config=config, language=lang, db_mapper=ProductDbMapper(sql_db))
    # Save order to DB:
    to_day = datetime.date.today()
    order_obj = DataObject("orders", {"customer": user_id, "order_date": to_day})
    order_id = sql_db.insert(order_obj)
    for item in order_items:
        amnt = order_items[item]
        item_obj = DataObject("order_items", {"order_id": order_id, "item_id": item[2], "amount": amnt})
        item_id = sql_db.insert(item_obj)

    print()
    print("Quittung")
    sum_all = OUTPUT_MGMT.print_receipt(order_items)
    print (f"Vielen Dank f??r Ihre Bestellung ??ber {sum_all} ??? und auf Wiedersehen!")
    # return anything?
    return order_items

def print_menu():
    print()
    print("\tOptions: ")
    print("\tq -> Quit this program.")
    print("\tenv -> Check environment.")
    print("\tdba -> Access DB administration.")
    print("\tweb -> Run the sample web application (web-a-casa).")
    print("\tgui -> Open admin GUI.")
    print("\ttest -> Test: Take order (life test via command line)")

def menu():
    ADMIN_LANGUAGE = "EN" # TODO Pass as program arg
    print("Acasa Restaurant Administration. ") # TODO logging
    while True:
        print_menu()
        user_choice = input("\n>")
        # Python 3.9 does not support 'switch' statement (up from 3.10)!!
        if user_choice == "q": 
                print("Leaving the program..")
                break
        elif user_choice == "env":
            print("Checking environment..")
            show_environment()
        elif user_choice == "dba":
            start_db_admin(config["csv_files"])
        elif user_choice == "web":
            print("Sorry, under construction!")
            #import sample
            #web_app, ctx_cache = create_web_server()
            # deployment must come before starting the Quart instance!!
            #sample.install_api(web_app, db_proxy, ctx_cache)
            # Running the ASGI runtime with uvicorn (should be similar to deploament on Heroku etc.)
            #runner = uvicorn.run(web_app, host="localhost", port=5000, log_level="info")
            #print("Running {}".format(runner))
        elif user_choice == "gui":
            print("Opening admin GUI") # TODO log
            start_admin_app()
        elif user_choice == "test":
            print("Starting order preview.")
            order = start_order_management(config, ADMIN_LANGUAGE, db_proxy)
            OUTPUT_MGMT.print_receipt(order)
        else:
            print("You've entered an invalid choice.")

menu() # main()

#############################################################################
# ACASA Customer Portal Web Application - Utility program to provide controls:
# A. Manage ASGI web server (deliver static files, RESTful web services etc.)
# B. Provide database access 
#############################################################################
#import importlib as imp
import os
import yaml
import pathlib
import redis
from quart import Quart, session, render_template
import uvicorn

THIS_PATH = pathlib.Path(__file__).parent
CONFIG_PATH = "{}{}{}".format(THIS_PATH.resolve(), os.sep, "config.yml")
DB_PATH = os.path.join(os.path.dirname(__file__), 'portal.db3')
SQL_PATH = pathlib.Path("{}{}acasa_schema.sql".format(THIS_PATH,os.sep))

with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
    cfg_text = openfile.read()
    config = yaml.safe_load(cfg_text)

# Provide a means to initialize the database and the web server;
# Things don't get started here.. Goal is to initialize properly!
# functionalized because of invocation from __init__.py, s.th.
def _init_controls(db_mod): 
    init_seq = 0
    db_name = config['database']['file_name']
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    global db_proxy # export (instead of getter function)
    db_proxy = db_mod.create_proxy(db_path)
    # Initialize (not start) Quart web server
    global web_app
    web_app = create_server(config['web'])
    RequestMapper(web_app)
    # Redis cache
    global cache 
    cache = redis.Redis()
    return init_seq

def create_server(web_config):
    """
    Quart initialization; must be done from main.py because the config.yaml sits there..
    From scaffold.py: 
    def __init__(
        self,
        import_name: str,
        static_url_path: Optional[str] = None,
        static_folder: Optional[str] = "static",
        static_host: Optional[str] = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: Optional[str] = "templates",
        instance_path: Optional[str] = None,
        instance_relative_config: bool = False,
        root_path: Optional[str] = None,
    ) 

    Returns:
        _type_: _description_
    """
    static_dir = pathlib.Path("{}{}{}".format(THIS_PATH, os.sep, web_config['static_folder']))
    template_dir = pathlib.Path("{}{}{}".format(THIS_PATH, os.sep, web_config['template_folder']))
    web_app_name = web_config['import_name']
    global web_app # export
    web_app = Quart(
        import_name = web_app_name,
        root_path = THIS_PATH,
        static_folder = static_dir.resolve(),
        static_url_path = "/",
        template_folder = template_dir.resolve()
    )
    web_app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    return web_app

_PROD_SQL = """SELECT p.name AS product_name, 
        p.price AS Product_price, 
        c.name AS category_name 
FROM products p, categories c 
WHERE p.category_id = c.id"""

class RequestMapper():
    """ Routing.
        - Deliver static files
        - Cache content
        - Provide 'RESTful' API (SQL-to-JSON mapping)
    """
    def _init_cache(self):
        prods = db_proxy.query(_PROD_SQL)
        prods_by_cat = dict()
        for p_name, p_price, p_category in prods:
            if not p_category in prods_by_cat:
                prods_by_cat[p_category] = list()
            prods_by_cat[p_category].append({"name": p_name, "price": p_price})
        self._prods = prods_by_cat # Cache all prods/categories in dict

    def _invalidate_cache(self):
        del self._prods

    def __init__(self, quart_inst: Quart):
        """_summary_
            Using this instance to cache some data; attention: DO NOT CHANGE INDENTATION!!
            TODO: Use Redis
        Args:
            quart_inst (Quart): _description_

        Returns:
            _type_: A RequestMapper object
        """
        self._init_cache()

        @quart_inst.before_request
        def make_session_permanent():
            session.permanent = True

        @quart_inst.route('/')
        async def index():
            return await render_template("index.html", 
                cats = list(self._prods))

        # TODO generate links according to self._prods dictionary!

        @quart_inst.route('/Pizzas')
        async def pizzas():
            pizzas = self._prods["Pizzas"]
            return await render_template("index.html", 
                cats = list(self._prods), 
                prods = pizzas)

        @quart_inst.route('/Drinks')
        async def drinks():
            drinks = self._prods["Drinks"]
            return await render_template("index.html", 
                cats = list(self._prods), 
                prods = drinks)

        @quart_inst.route('/Pasta')
        async def pasta():
            pasta = self._prods["Pasta"]
            return await render_template("index.html", 
                cats = list(self._prods), 
                prods = pasta)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        #                 REST!                      #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

        @quart_inst.route('/products/')
        async def list_products():
            _sql = """SELECT p.name AS product_name, 
                                p.price AS Product_price, 
                                c.name AS category_name 
                        FROM products p, categories c 
                        WHERE p.category_id = c.id
                        AND c.id = 
                        """
            prods = db_proxy.query(_sql)
            prod_by_cat = dict()
            for p_name, p_price, p_category in prods:
                if not p_category in prod_by_cat:
                    prod_by_cat[p_category] = list()
                prod_by_cat[p_category].append({"name": p_name, "price": p_price})
            return prod_by_cat # Automatic JSON converting! :-)

###################
# Utility methods #
###################

# Initialize the database schema. The schema file resides in the current directory and 
# must be splitted into a set of strings that are executed in their own transaction (no bulk).
def init_db():
    sql_stmts = list()
    with open(SQL_PATH, mode = "r", encoding = "UTF-8") as sql:
        current_str = ""
        for line in sql.readlines():
            if line.startswith("--"): continue
            elif line.rfind(";") > 0:
                left_str, right_str = line.split(";")
                sql_stmts.append(current_str + left_str) # no strip, line break is in right string
                current_str = ""
            else:
                current_str += line.strip("\n") # remove Zeilenumbruch    
   
    for sql_stmt in sql_stmts:
        res_code = db_proxy.execute_sql(sql_stmt)
        print("SQL executed: {}, result is: {}".format(sql_stmt, res_code))

###############################################################################
# Executed when this script gets loaded.. (compare __init__.py in this folder!)
###############################################################################

def run_test_suite():
   print("Running tests..")

def main(): # Provide user control via cmd line input
    while True:
        print("This is the main program. Enter 't' to run the test suite,\
            'd' to run the Quart server in DEBUG mode, 's' to start the web server with uvicorn. \
            \nEnter 'z' to leave the program.")
        user_input = input("\n>")
        if user_input == 'z': break
        elif user_input == 't': # run test suite (TODO) 
            run_test_suite()
        elif user_input == 'd': # debug 
            web_app.run()
        elif user_input == 's': # start uvicorn server
            uvicorn.run("__main__:web_app", host=config["web"]["host_name"], port=config["web"]["host_port"], log_level="info")

if __name__ == "__main__":
    print("Startup script called on ACASA main directly - checking parameters set..")
    # import in script-self didn't work!! (Package problem??)
    import db as db_mod
    _init_controls(db_mod)
    main()

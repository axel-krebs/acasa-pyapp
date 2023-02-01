#############################################################################
# ACASA Customer Portal Web Application - Utility program to provide controls:
# A. Manage ASGI web server (deliver static files, RESTful web services etc.)
# B. Provide database access 
#############################################################################
#import importlib as imp
import os
import yaml
import pathlib
from quart import Quart, render_template

THIS_PATH = pathlib.Path(__file__).parent
CONFIG_PATH = "{}{}{}".format(THIS_PATH.resolve(), os.sep, "config.yml")
DB_PATH = os.path.join(os.path.dirname(__file__), 'portal.db3')
SQL_PATH = pathlib.Path("{}{}acasa_schema.sql".format(THIS_PATH,os.sep))

with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
    cfg_text = openfile.read()
    config = yaml.safe_load(cfg_text)

# Provide a means to initialize the database and web server;
# Things don't get started here.. Goal is to initialize properly!
# modularized because of invocation from __init__.py, s.th.
def _init_controls(db_mod): 
    init_seq = 0
    db_name = config['database']['file_name']
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    global db_proxy # export
    db_proxy = db_mod.create_proxy(db_path)
    
    return init_seq

def create_server(web_config):
    """
    Quart initialization; muust be done from main.py because the config.yaml sits there..
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

class RequestMapper():
    
    def __init__(self, quart_instance: Quart):

        @quart_instance.route('/')
        async def index():
            return await render_template('index.html')

        @quart_instance.route('/products/')
        async def list_products():
            _sql = "SELECT * FROM products"
            prods = db_proxy.query(_sql)
            return 'products'

###################
# Utility methods #
###################

# The schema file resides in the current directory and must be splitted into a 
# set of strings;
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
   pass

def main():
    while True:
        print("This is the main program. Enter 'z' to leave the program, 't' to run the test suite, \
            's' to run the Quart server in DEBUG mode.")
        user_input = input("\n>")
        if user_input == 'z': break
        elif user_input == 't':
            run_test_suite()
        elif user_input == 's':
            create_server(config['web'])
            RequestMapper(web_app)
            web_app.run()

if __name__ == "__main__":
    print("Startup script called on ACASA main directly - checking parameters set..")
    # import in script didn't work!! (Package problem??)
    import db as db_mod
    _init_controls(db_mod)
    main()

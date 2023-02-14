#############################################################################
# Utility program to provide controls for the web object (Quart instance):
# 1. Manage ASGI web server (debug, run on Uvicorn server etc.)
# 2. Provide database access to configuration database (i18n etc.)
#############################################################################
import os
import yaml
from pathlib import Path
from quart import Quart, session, render_template
from tinydb import TinyDB, Query
import uvicorn
from acasa_web.web import Deployment

THIS_PATH = Path(__file__).parent
CONFIG_PATH = "{}{}{}".format(THIS_PATH.resolve(), os.sep, "config.yml")

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
    static_dir = Path("{}{}{}".format(THIS_PATH, os.sep, web_config['static_folder']))
    template_dir = Path("{}{}{}".format(THIS_PATH, os.sep, web_config['template_folder']))
    web_app_name = web_config['import_name']
    web_app = Quart(
        import_name = web_app_name,
        root_path = THIS_PATH,
        static_folder = static_dir.resolve(),
        static_url_path = "/",
        template_folder = template_dir.resolve()
    )
    web_app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    return web_app

def install_cache():
    # check environment for availability of caching layer
    # global cache 
    # Redis cache
    #cache = redis.Redis()
    pass

def deploy_unit(unit: Deployment):
    """_summary_
        Executes inject on the unit object (inversion of control)
    Args:
        unit (Deployment): _description_
    """
    unit.apply(web_app, render_template)

###############################################################################
# Executed when this script gets loaded.. (compare __init__.py in this folder!)
###############################################################################

def run_test_suite():
   print("Running tests..")

def start_server():
    uvicorn.run("{}:web_app".format(__name__), host=config["web"]["host_name"], port=config["web"]["host_port"], log_level="info")

def menu(): # Provide user control via cmd line input
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
            start_server()

with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
    cfg_text = openfile.read()
    config = yaml.safe_load(cfg_text)

web_app = create_server(config['web']) # 'exported' automatically when module loaded

if __name__ == "__main__":
    print("Startup script called on ACASA main directly - Opening menu()")
    menu()

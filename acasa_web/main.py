#############################################################################
# ACASA Customer Portal Web Application - Utility program to provide controls:
# A. Manage ASGI web server (deliver static files, RESTful web services etc.)
# B. Provide database access 
#############################################################################
#import importlib as imp
import os
import yaml
import pathlib

THIS_PATH = pathlib.Path(__file__).parent
CONFIG_PATH = "{}{}{}".format(THIS_PATH.resolve(), os.sep, "config.yml")
DB_PATH = os.path.join(os.path.dirname(__file__), 'portal.db3')

with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
    cfg_text = openfile.read()
    config = yaml.safe_load(cfg_text)

# Provide a means to initialize the database and web server;
# Things don't get started here.. Goal is to initialize properly!
# modularized because of invocation from __init__.py, s.th.
def _init_controls(web_mod,db_mod): 
    global db_proxy, web_ctl
    init_seq = 0
    web_ctl = web_mod.WebController(config)
    db_name = config['database']['file_name']
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    db_proxy = db_mod.create_proxy(db_path)
    web_ctl.create_routes(db_proxy)
    return init_seq

######################################################
# Accessors provided via module import
######################################################

def get_web_controller():
    return web_ctl 

def get_db_proxy():
    return db_proxy

###############################################################################
# Utility methods
###############################################################################

def create_db_schema():
    pass

################################################################################
# Executed when this script gets loaded.. (compare __init__.py in this folder!)
################################################################################

if __name__ == "__main__":
    print("Startup script called on ACASA web directly - checking parameters set..")
    # import in script didn't work!! (Package problem??)
    import web as web_mod
    import db as db_mod
    _init_controls(web_mod,db_mod)
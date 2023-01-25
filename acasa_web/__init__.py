# Package import (proxy for 'main.py')
# 1. Load config files
# 2. Initialize DB (db.py) and WebController (web.py)
# 3. provide access to controller
from . import db as db_mod
from . import web as web_mod
from . import main

web_ctl, db_proxy = main._init_controls(web_mod,db_mod)

######################################################
# Accessors provided via module import
######################################################

def get_web_controller()  -> web_mod.WebController:
    return web_ctl 

def get_db_proxy() -> db_mod.Facade:
    return db_proxy
# Package import (proxy for 'main.py')
# 1. Load config files
# 2. Initialize DB (db.py) and WebController (web.py)
# 3. provide access to controller
from . import db as db_mod
from . import web as web_mod
from . import main 
main._init_controls(web_mod,db_mod)

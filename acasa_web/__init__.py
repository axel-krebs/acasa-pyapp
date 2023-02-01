# Package import (proxy for 'main.py')
# 1. Load config files
# 2. Initialize DB (db.py) and WebController (web.py)
# 3. provide access to controller
from . import db as db_mod
from . import main 
main._init_controls(db_mod)

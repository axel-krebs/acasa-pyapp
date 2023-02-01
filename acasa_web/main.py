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
SQL_PATH = pathlib.Path("{}{}acasa_schema.sql".format(THIS_PATH,os.sep))

with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
    cfg_text = openfile.read()
    config = yaml.safe_load(cfg_text)

# Provide a means to initialize the database and web server;
# Things don't get started here.. Goal is to initialize properly!
# modularized because of invocation from __init__.py, s.th.
def _init_controls(web_mod,db_mod): 
    global db_proxy, web_ctl
    init_seq = 0
    web_ctl = web_mod.create_server(config)
    db_name = config['database']['file_name']
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    db_proxy = db_mod.create_proxy(db_path)
    #web_ctl.create_routes(db_proxy)
    return init_seq

######################################
# Accessors provided via module import
######################################

def get_web_controller():
    return web_ctl 

def get_db_proxy():
    return db_proxy

# Associate routes (REST) with DB calls
def assign_routes():
    pass

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
        print("This is the main program. Enter 'z' to leave the program, 't' to run the test suite, 'w' to debug Quart server")
        user_input = input("\n>")
        if user_input == 'z': break
        elif user_input == 't':
            run_test_suite()
        elif user_input == 's':
            web_ctl.create_routes(db_proxy)
            web_ctl.debug()

if __name__ == "__main__":
    print("Startup script called on ACASA web directly - checking parameters set..")
    # import in script didn't work!! (Package problem??)
    import web as web_mod
    import db as db_mod
    _init_controls(web_mod,db_mod)
    main()
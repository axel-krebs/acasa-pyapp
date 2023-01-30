# Restaurant ACASA
import test
import yaml
import os
import errors as ERR
from pathlib import Path
import csv
from license_management import *
from acasa_backoffice.output_management import *
from order_management import *
from acasa_admin.admin_gup import start_admin_app

os.chdir(Path(__file__).parent)

SCRIPT_PATH = Path(__name__).parent.resolve()
SQL_PATH = Path("{}{}acasa_schema.sql".format(SCRIPT_PATH,os.sep))

def load_config() -> dict:
    """ Load the menu from a YAML file.
        TODO: Make this function private to this script.. ;-)
    Raises:
        ERR.LicenseError: ;-)

    Returns:
        dict: The configuration as dict.
    """
    with open("./acasa.yml", mode = "r", encoding = "UTF-8") as openfile:
        cfg_text = openfile.read()
        config = yaml.safe_load(cfg_text)
        if not check_valid(config["license_key"]):
            raise ERR.LicenseError("Your license has probably expired.. :-)")
    return config

# Depricated: to be replaced by customer portal
def start_order_management(config, lang):
    order = take_order(config, lang) # TODO pass language as program arg!
    print()
    print("Quittung")
    sum_all = print_receipt(order)
    print (f"Vielen Dank für Ihre Bestellung über {sum_all} € und auf Wiedersehen!")
    # return anything?
    return order

# The schema file must be splitted into a set of strings;
# eventually move this to an SQL parsing utility (maybe db.py?)
def load_db_schema() -> list:
    statements = list()
    with open(SQL_PATH, mode = "r", encoding = "UTF-8") as sql:
        current_str = ""
        for line in sql.readlines():
            if line.startswith("--"): continue
            elif line.rfind(";") > 0:
                left_str, right_str = line.split(";")
                statements.append(current_str + left_str) # no strip, line break is in right string
                current_str = ""
            else:
                current_str += line.strip("\n") # remove Zeilenumbruch          
    return statements

def load_csv(file_path: Path, fn: list) -> list:
    ret_list = []
    with open(file_path,mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file, fieldnames=fn, delimiter="|")
        next(csv_reader) # skip headers
        for line in csv_reader:
            ret_list.append(line)
    return ret_list

def start_db_admin(db_controller):
    while True:
        print("You're in DB admin. Pls. choose from following operations:")
        print("\t0. Quit DB admin.")
        print("\t1. Initialize database (schema creation).")
        print("\t2. Load data from CSV.")
        print("\t3. Enter custom SQL.")
        user_choice = input("\t>")
        if user_choice == '0':
            break
        elif user_choice == '1':
            sql_stmts = load_db_schema()
            for sql_stmt in sql_stmts:
                res_code = db_controller.execute_sql(sql_stmt)
                print("SQL executed: {}, result is: {}".format(sql_stmt, res_code))
        elif user_choice == '2':
            print("Loading files.. ")
            # specify format of CSV file: attributes must be in given list!
            csv_files = [
                ("categories",["ID","NAME"]),
                ("products",["ID","NAME","PRICE","CATEGORY_ID"]),
                ("customers",["ID","NAME","EMAIL","PASS_WORD"])
            ]
            for file_def in csv_files:
                entity_name = file_def[0]
                cols = file_def[1]
                csv_file_path = "{}{}{}.csv".format(SCRIPT_PATH.resolve(), os.sep, entity_name)
                res_csv = load_csv(csv_file_path, cols)

                # convert to SQL string; TODO move this code to a mapping facade object!
                for data_set in res_csv:
                    
                    # send to controller
                    sql_code = db_controller.upsert(entity_name, data_set, "id")
                    print("SQL returned: ", sql_code)
        elif user_choice == '3':
            custom_sql = input("SQL>")
            res_csv = db_controller.execute_sql(custom_sql)
            print("SQL executed: {}, result is: {}".format(custom_sql, res_csv))

def main():
    config = load_config()
    admin_language = "EN"
    print("Acasa Restaurant Administration. ") # TODO logging
    print("\tOptions: ")
    print("\t0. Quit this program.")
    print("\t1. DB administration")
    print("\t2. Access customer portal (web).")
    print("\t3. Open admin GUI.")
    print("\t4. Test-bed: Take order (life test via command line)")
    while True:
        user_choice = input("\n>")
        # Python 3.9 does not support 'switch' statement (up from 3.10)!!
        if user_choice == "0": 
                print("Leaving the program..")
                break
        elif user_choice == "1":
            from acasa_web import main # lazy loading allowed here..
            db_facade = main.get_db_proxy()
            start_db_admin(db_facade)
        elif user_choice == "2":
            from acasa_web import main # lazy loading allowed here..
            web_controller  = main.get_web_controller()
            # TODO Provide commands for controllers
        elif user_choice is "3":
            print("Opening admin GUI") # TODO log
            start_admin_app()
        elif user_choice is "4":
            print("Starting order preview.")
            order = start_order_management(config, admin_language)
            print_receipt(order)
        else:
            print("You've entered an invalid choice.")
                
main()
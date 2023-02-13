#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Restaurant ACASA client utitlities
import test
import yaml
import os
import errors as ERR
from pathlib import Path
import csv
import pandas as pd
from license_management import *
from output_management import *
from order_management import *
from acasa_admin.admin_gup import start_admin_app

os.chdir(Path(__file__).parent)

SCRIPT_PATH = Path(__name__).parent.resolve()

# Metadata for CSV-import files: attributes must be in the given list!
# Format: {table_name => [attribute1, attribute2, etc.]}
CSV_FILES = [
    ("categories",["ID","NAME"]),
    ("products",["ID","NAME","PRICE","CATEGORY_ID"]),
    ("customers",["ID","NAME","EMAIL","PASS_WORD"])
]

def show_environment():
    print("Pandas: ", pd.__version__)
    print("CSV: ", csv.__version__)
    
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


def start_db_admin(main):
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
            main.init_db()     
        elif user_choice == '2':
            print("Loading files.. ")
            db_controller = main.db_proxy # get hold of DB controller (facade)
            for file_def in CSV_FILES:
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

# Depricated! TODO Introduce integration tests
def start_order_management(config, lang):
    order = take_order(config, lang) # TODO pass language as program arg!
    print()
    print("Quittung")
    sum_all = print_receipt(order)
    print (f"Vielen Dank für Ihre Bestellung über {sum_all} € und auf Wiedersehen!")
    # return anything?
    return order

def load_csv(file_path: Path, fn: list) -> list:
    ret_list = []
    with open(file_path,mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file, fieldnames=fn, delimiter="|")
        next(csv_reader) # skip headers
        for line in csv_reader:
            ret_list.append(line)
    return ret_list

def print_menu():
    print("\tOptions: ")
    print("\tq -> Quit this program.")
    print("\tenv -> Check environment.")
    print("\tdba -> Access DB administration.")
    print("\tweb -> Access customer portal (web).")
    print("\tgui -> Open admin GUI.")
    print("\ttest -> Test: Take order (life test via command line)")

def menu():
    config = load_config()
    admin_language = "EN"
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
            from acasa_web import main # lazy loading allowed here..
            start_db_admin(main)
        elif user_choice == "web":
            from acasa_web import main # lazy loading allowed here..
            web_controller  = main.web_app
            # TODO Provide commands for controllers
        elif user_choice == "gui":
            print("Opening admin GUI") # TODO log
            start_admin_app()
        elif user_choice == "test":
            print("Starting order preview.")
            order = start_order_management(config, admin_language)
            print_receipt(order)
        else:
            print("You've entered an invalid choice.")
                
menu()
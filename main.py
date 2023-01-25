# Restaurant ACASA
import test
import yaml
import os
import errors as ERR
from pathlib import Path
from license_management import *
from acasa_backoffice.output_management import *
from order_management import *
from acasa_admin.admin_gup import start_admin_app

os.chdir(Path(__file__).parent)

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
    
def main():
    config = load_config()
    admin_language = "EN"
    print("Acasa Restaurant Administration. ") # TODO logging
    print("Options: ")
    print("0. Quit this program.")
    print("1. Access customer portal.")
    print("2. Check DB runnig smoothely..")
    print("3. Open Admin GUI.")
    print("4. Take order (life test via command line)")
    while True:
        user_choice = input(">")
        # Python 3.9 does not support 'switch' statement (up from 3.10)!!
        if user_choice is "0": 
                print("Leaving the program..")
                break
        elif user_choice is "1":
            import acasa_web # lazy loading allowed here..
            web_controller = acasa_web.get_web_controller()
            db_facade: acasa_web.db_mod.Facade = acasa_web.get_db_proxy()
            res = db_facade.query_db("CREATE TABLE IF NOT EXISTS repertoire(id DECIMAL, name VARCHAR(50), price DECIMAL)")
            # TODO Provide commands for controllers

        elif user_choice is "2":
            print("CSV import")
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
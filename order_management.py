# ACASA Order management
# @Depricated! Will be replaced be Customer Portal Web Application (web)

def print_menu(repertoire: dict, messages: dict, currency_symbol: str = "€") -> dict:
    """Print the menu to screen.

    Args:
        repertoire (dict): Data containing the 'repertoire' and other settings of the company.
        messages (dict): Data containing messages shown to the user.
        currency_symbol: The currency symbol

    Returns:
        dict: A new dictionary that has the repertoire sorted by 'id' for better ordering, e.g. {"100": (Pizza Margarita,5.0)}
    """
    print(50*"~")
    print(25*" ","Menu")
    print(50*"~")
    print()
    available_today = {} # restructured menu for selection of item per key like {"100": (Pizza Margarita,5.0)} etc.
    for category in repertoire:
        print(category) # prints key
        print(len(category)*"~")
        print()
        for dish in repertoire[category]:
            dish_fomratted = "  {}. {} à {}/{}".format(dish["id"], dish["name"], str(dish["price"]) + currency_symbol, messages['msr'])
            print(dish_fomratted)
            available_today[str(dish["id"])] = dish["name"], dish["price"] # For simplicity, fill the 'available' dict here..
                                                                           # convert the id to string to avoid casting user input
    print()
    return available_today

def take_order(config: dict, language: str = "DE") -> dict:
    """Prints available items and takes user input.

    Args:
        config (dict): A configuration
        language (str, optional): The messgaes dictionary. Defaults to "DE".

    Returns:
        dict: A list of ordered items with amount (dictionary).
    """
    user_selection = {} # memoize user input, like {('Pizza Margerita',5.0,100):3} (3 = three pcs.)
    user_choice = '~upps!'
    repertoire = config['repertoire']
    messages = config['messages'][language]
    avail = print_menu(repertoire, messages, currency_symbol = config['billing']['currency'])
    while True:
        if user_choice is 'w': # User entered unknown order number but does not want to continue
            break
        bestell_nr = input(messages['what_to_order'].join(" >"))
        if bestell_nr == "0":
            break
        elif bestell_nr in avail: # 'in' gives the keys for dict, so no need to call .getKeys() method
            bestell_anz = int(input(messages['how_many'].join(" >")))
            user_selection[(*avail[bestell_nr],bestell_nr)] = bestell_anz # pack key as tuple
        else: 
            user_choice = input(messages['unrecognized_input'].format(bestell_nr).join(" >"))
            if user_choice is '':
                continue
    return user_selection
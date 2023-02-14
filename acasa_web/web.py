# Shared web objects
from quart import Quart, session, render_template

class Deployment():
    """ Routing.
        - Deliver static files
        - Cache content
        - Provide 'RESTful' API (SQL-to-JSON mapping)
    """

    def __init__(self):
        """_summary_
            Using this instance to cache some data; attention: DO NOT CHANGE INDENTATION!!
            TODO: Use Redis
        Args:
            quart_inst (Quart): _description_

        Returns:
            _type_: A RequestMapper object
        """
        #@quart_inst.before_request
        #def make_session_permanent():
        #    session.permanent = True

if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import'.")
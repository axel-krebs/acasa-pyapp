# ACASA web 
from quart import Quart, render_template

class WebController(): # 'wrapper' around Quart
    """_summary_
        Provide a wrapper around the Quart instances.
    """

    def __init__(self, config: dict): # 'constructor'
        self._config = config
        self._quart = Quart(__name__)
    
    def create_routes(self, db_facade): # Attention 

        @self._quart.route('/')
        async def index():
            return await render_template('index.html')

        @self._quart.route('/products/')
        async def list_products():
            ps = db_facade.get_products()
            return 'products'

        # TODO change route definition -> mapping JSON requests to database calls

        return self # fluent I/F

    def start(self): # public
       self._quart.run()
       return self # fluent I/F

    def stop(self):
        del self._quart
        return self # fluent I/F

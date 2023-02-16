# Example web mapping 
from web import Deployment
from db import DbInstance

_PROD_SQL = """SELECT p.name AS product_name, 
   p.price AS Product_price, 
   c.name AS category_name 
FROM products p, categories c 
WHERE p.category_id = c.id"""

class SampleDeployment(Deployment):

        def __init__(self, db_inst: DbInstance):
                self._db_inst = db_inst
                self._init_cache()

        def _init_cache(self):
                prods = self._db_inst.query(_PROD_SQL)
                prods_by_cat = dict()
                for p_name, p_price, p_category in prods:
                        if not p_category in prods_by_cat:
                                prods_by_cat[p_category] = list()
                        prods_by_cat[p_category].append({"name": p_name, "price": p_price})
                self._prods = prods_by_cat # Cache all prods/categories in dict

        def _invalidate_cache(self):
                del self._prods
           
        def apply(self, asgi_RT, render_func): # overridden
                
                @asgi_RT.route('/')
                async def index():
                        return await render_func("index.html", cats = list(self._prods))

                # TODO generate links according to self._prods dictionary!

                @asgi_RT.route('/Pizzas')
                async def pizzas():
                        pizzas = self._prods["Pizzas"]
                        return await render_func("index.html", 
                                cats = list(self._prods), 
                                prods = pizzas)

                @asgi_RT.route('/Drinks')
                async def drinks():
                        drinks = self._prods["Drinks"]
                        return await render_func("index.html", 
                                cats = list(self._prods), 
                                prods = drinks)

                @asgi_RT.route('/Pasta')
                async def pasta():
                        pasta = self._prods["Pasta"]
                        return await render_func("index.html", 
                                cats = list(self._prods), 
                                prods = pasta)

                @asgi_RT.route('/products/')
                async def list_products():
                        _sql = """SELECT p.name AS product_name, 
                                                p.price AS Product_price, 
                                                c.name AS category_name 
                                        FROM products p, categories c 
                                        WHERE p.category_id = c.id
                                        AND c.id = 
                                        """
                        prods = self._db_inst.query(_sql)
                        prod_by_cat = dict()
                        for p_name, p_price, p_category in prods:
                                if not p_category in prod_by_cat:
                                        prod_by_cat[p_category] = list()
                                        prod_by_cat[p_category].append({"name": p_name, "price": p_price})
                        return prod_by_cat # Automatic JSON converting! :-)

def create_deployment(db_instance):
     return SampleDeployment(db_instance)

if __name__ == "__main__":
    print("This is a deployment unit and cannot be run directly! Usage:")
    print("""from sample import create_deployment
             deployment1 = create_deployment(db_proxy)
             web_inst_1.deploy(deployment1)
          """)
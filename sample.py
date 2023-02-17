# Example web mapping 
from web import Deployment, Documentstore, ContextCache
from db import DbInstance

_PROD_SQL = """SELECT p.name AS product_name, 
                        p.price AS Product_price, 
                        c.name AS category_name 
                FROM products p, categories c 
                WHERE p.category_id = c.id"""

class AcasaWebStore(Documentstore):

        def __init__(self, acasa_db):
                self._db = acasa_db

        def test_impl(self):
                pass

        def get_user_for_cookie(self, cookie):
                self._db.aql.execute('FOR doc IN WebUsers RETURN doc')
    
        def create_user(self, name: str = "", email: str = ""):
                pass

class SampleDeployment(Deployment):

        def __init__(self, db_inst: DbInstance):
                self._db_inst = db_inst

        def _init_cache(self, cache: dict):
                prods = self._db_inst.query(_PROD_SQL)
                prods_by_cat = dict()
                for p_name, p_price, p_category in prods:
                        if not p_category in prods_by_cat:
                                prods_by_cat[p_category] = list()
                        prods_by_cat[p_category].append({"name": p_name, "price": p_price})
                cache['prods'] = prods_by_cat # Cache all prods/categories in dict
                cache['cats'] = prods_by_cat.keys() # convenience for usage in web template
                #return cache
          
        def apply(self, asgi_RT, cache, render_func): # overridden
                
                self._init_cache(cache)

                @asgi_RT.route('/Pizzas')
                async def pizzas():
                        return await render_func("pizzas.html", 
                                                 pizzas=cache['prods']["Pizzas"],
                                                 cache_data=cache) # TODO not so nice..
                                                                   # Generally put all rendering of templates back to Deployer!
                
                @asgi_RT.route('/Drinks')
                async def drinks():
                        return await render_func("drinks.html", 
                                                 drinks=cache['prods']["Drinks"],
                                                 cache_data=cache)

                @asgi_RT.route('/Pasta')
                async def pasta():
                        return await render_func("pasta.html", 
                                                 pasta=cache['prods']["Pasta"],
                                                 cache_data=cache)

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

def create_deployment(db_instance, ctx_cache):
     return SampleDeployment(db_instance)

if __name__ == "__main__":
    print("This is a deployment unit and cannot be run directly! Usage:")
    print("""from sample import create_deployment
             deployment1 = create_deployment(db_proxy)
             web_inst_1.deploy(deployment1)
          """)
# Example web mapping
from web import ContextCache
from db import DbInstance


class Category():
    pass


class Product():
    pass


def install_api(asgi_RT, db_instance: DbInstance, ctx_cache: ContextCache):

    @asgi_RT.route('/products/')
    async def list_products():
        _sql = """SELECT 
                        p.name AS product_name, 
                        p.price AS product_price, 
                        c.name AS category_name 
                FROM products p, categories c 
                WHERE p.category_id = c.id
                """
        prods = db_instance.query(_sql)
        prod_by_cat = dict()
        for p_name, p_price, p_category in prods:
            if not p_category in prod_by_cat:
                prod_by_cat[p_category] = list()
            prod_by_cat[p_category].append({"name": p_name, "price": p_price})
        return prod_by_cat  # Automatic JSON converting! :-)


if __name__ == "__main__":
    print("This is a deployment unit and cannot be run directly! Usage:")
    print("""from sample import create_deployment
             deployment1 = create_deployment(db_proxy)
             web_inst_1.deploy(deployment1)
          """)

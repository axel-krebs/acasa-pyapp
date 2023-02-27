# Example web mapping
from web import ContextCache
from db import *

# 'Domain objects'
@PersistenceCapable(table_name="categories")
class Category():

    @Column(col_name="id", sql_type=ColumnTypes.INTEGER)
    def _id(self) -> int: 0

    @Column(col_name="name", sql_type=ColumnTypes.TEXT)
    def _name(self) -> str: ""

@PersistenceCapable()
class Products():
    
    @Column()
    def id() -> int: 0

    name: str
    price: float
    category: Category

cat1 = Category("Drinks")
cat1._name = "Drinks"
what = cat1._name

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
    print("""from sample import install_api
             install_api(web_instance, db_proxy, ctx_cache)
          """)

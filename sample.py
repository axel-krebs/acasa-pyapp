# Example web mapping
from web import ContextCache
from db import *

# 'Domain objects'


# "table_name" MUST be a keyword-based parameter, otherwise the "normal" ctor of the class will not be working!s
@PersistenceCapable(table_name="categories")
class Category():

    @Column(col_name="id", sql_type=ColumnTypes.INTEGER)
    def id() -> int:
        return 0  # "0" will be the default value

    @Column(col_name="name", sql_type=ColumnTypes.TEXT)
    def name() -> str:  # Function name will be replaced, as well as return value type
        print("Hallo")  # Will be discarded!
        # return "" - implicit!

    # Make sure that custom class methods won't get lost when class is "decorated"..
    def custom_method(self):
        print("Method without decorator invoked, value of name2:",
              self.name2)  # attribute correctly set??


@PersistenceCapable(table_name="products")
class Product():

    @Column() # colummn name inferred from method signature
    def id() -> int:
        return 0.0

    @Column()
    def name() -> str:
        return ""

    @Column()
    def price() -> float:
        return 0.0

    # @Join(join_type=JoinType.LEFT)
    @Column()
    def category() -> Category:
        return None


cat2 = Category("Holla")
cat2.name = "Drinks"
print(cat2.name)
cat2.name2 = "Drink$_2"  # Additional attributes allowed, though not nice..
cat2.custom_method()

Category.findAll()

# I have a key, pls. load the product
p1 = Product.load(1)
#p1.price = 5.99
p1.save()

pizza_margerita = Product("Pizza Margerita")
pizza_margerita.price = 4.99
pizza_margerita.save()


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

# Example web mapping
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from web import ContextCache
from db import *

class Application(containers.DeclarativeContainer):
    
    config = providers.Configuration()


# "table_name" MUST be a keyword-based parameter, otherwise the "normal" ctor of the domain class would not be working!
@PersistenceCapable(table_name="categories")
class Category():

    @Column(col_name="id", sql_type=ColumnTypes.INTEGER, primary_key=True)
    def id() -> int:
        return 0  # "0" will be the default value

    @Column(col_name="name", sql_type=ColumnTypes.TEXT)
    def name() -> str:  # Function name will be replaced, as well as return value type
        print("Hallo")  # Everything done here will be discarded!
        # return "" - implicitly None

    # Make sure that custom class methods won't get lost when class is "decorated"..
    def custom_method(self):
        print("Method without decorator invoked, value of name2:",
              self.name2)  # attribute correctly set??


@PersistenceCapable(table_name="products")
class Product():

    @Column()  # colummn name inferred from method signature
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


def install_api(asgi_RT, db_instance: SQLiteInstance, ctx_cache: ContextCache):

    set_relational_persistence_manager(db_instance) # "Injection".. TODO use 'dependency-injector' F/W

    cat2 = Category()
    cat2.name = "Exotic"
    cat2.id = 1001
    print(cat2)
    cat2.name2 = "Drink$_2"  # Additional attributes allowed, though ignored!
    cat2.custom_method()
    cat2.save()

    pizzaCat = Category.load(id=2000)
    pizzaCat.name = "Pizzen"
    pizzaCat.save()

    # I have a key, pls. load the product no. 1
    #p1 = Product.load(1)
    #p1.price = 5.99
    #p1.save()

    #pizza_margerita = Product(name="Pizza Margerita")
    #pizza_margerita.price = 4.99
    #pizza_margerita.save()

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

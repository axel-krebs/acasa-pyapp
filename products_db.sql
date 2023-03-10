-- schema creation; prevent data deletion using 'IF NOT EXISTS' - to DROP, use custom statements!
-- Multiple statements _must_ be delimited by semicolon, otherwise SQL parser will not work!
/**
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    pass_word TEXT NULL
);
**/
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL,
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
--ALTER TABLE ADD CONSTRAINT name_exists CHECK category IN ['Pizza'];
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL, 
    status INTEGER NOT NULL DEFAULT 0,
    order_date DATE
);
CREATE TABLE order_items (
    order_id INTEGER,
    item_id INTEGER,
    amount INTEGER,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (item_id) REFERENCES products(id)
    PRIMARY KEY (order_id,item_id)
);

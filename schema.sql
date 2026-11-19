DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS sales_raw;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id    INTEGER PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    region         TEXT NOT NULL,
    segment        TEXT NOT NULL,
    signup_date    TEXT
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    unit_price    REAL NOT NULL,
    unit_cost     REAL NOT NULL
);

-- Raw export exactly as received: no rules, may contain bad rows.
CREATE TABLE sales_raw (
    order_id     TEXT,
    order_date   TEXT,
    customer_id  INTEGER,
    product_id   INTEGER,
    quantity     INTEGER,
    discount     REAL
);

-- Clean, validated table that every report will read from.
CREATE TABLE sales (
    order_id     TEXT PRIMARY KEY,
    order_date   TEXT    NOT NULL,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id   INTEGER NOT NULL REFERENCES products(product_id),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    discount     REAL    NOT NULL DEFAULT 0,
    revenue      REAL    NOT NULL,
    profit       REAL    NOT NULL
);

CREATE INDEX idx_sales_date     ON sales(order_date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_product  ON sales(product_id);
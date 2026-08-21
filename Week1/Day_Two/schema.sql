-- Day 2 · Lab 2 — sample sales schema
--
-- Deliberately shaped like a real landing zone rather than a textbook model:
--
--   * orders has NO primary key on order_id. Corrections arrive as a second row
--     with the same order_id and a later updated_at. Deduplicating that is Q7.
--   * price_history is a slowly changing dimension. The price of a product
--     depends on when the order was placed, not on what the price is today.
--     That is Q11, and it is the query most people get wrong.
--   * order_items is one-to-many against orders, which is what makes the
--     fan-out trap in Q3 possible.
--   * region and status are denormalised onto the tables that use them so the
--     joins stay readable — a real model would normalise both.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    customer_name TEXT    NOT NULL,
    region        TEXT    NOT NULL,
    signup_date   TEXT    NOT NULL,          -- ISO date
    credit_limit  REAL                        -- deliberately NULL for some rows
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    discontinued INTEGER NOT NULL DEFAULT 0
);

-- Slowly changing dimension, Type 2 shape.
-- valid_to is exclusive and '9999-12-31' means "current".
CREATE TABLE price_history (
    product_id  INTEGER NOT NULL,
    valid_from  TEXT    NOT NULL,
    valid_to    TEXT    NOT NULL,
    unit_price  REAL    NOT NULL,
    PRIMARY KEY (product_id, valid_from)
);

-- No primary key on order_id, on purpose. Corrections arrive as new rows.
CREATE TABLE orders (
    order_row_id INTEGER PRIMARY KEY,        -- surrogate, technical only
    order_id     TEXT    NOT NULL,           -- the business key, NOT unique
    customer_id  INTEGER NOT NULL,
    order_date   TEXT    NOT NULL,
    status       TEXT    NOT NULL,           -- placed | shipped | cancelled
    updated_at   TEXT    NOT NULL,           -- the correction timestamp
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      TEXT    NOT NULL,
    product_id    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);

-- Indexes are created separately by seed.py so that Q12 can measure the
-- difference an index makes. Do not add them here.

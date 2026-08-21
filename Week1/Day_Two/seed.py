"""Build the lab database. Deterministic — same data every time, on every machine.

    python seed.py            # builds sales.db
    python seed.py --small    # builds a 5,000-order database for quick iteration

The seed is fixed at 42 so that every expected value in tests/test_queries.py is
stable. If you change anything in here, the tests will fail and they are supposed
to — regenerate the expected values deliberately rather than loosening the tests.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 42
DB_PATH = Path(__file__).parent / "sales.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = ["Widgets", "Gadgets", "Fittings", "Consumables", "Tools", "Spares"]
FIRST = ["Ravi", "Priya", "Anil", "Sunita", "Mohan", "Kavita", "Deepak", "Sneha",
         "Arjun", "Lata", "Vikram", "Meera", "Rahul", "Divya", "Karthik", "Anita"]
LAST = ["Kumar", "Sharma", "Verma", "Rao", "Das", "Nair", "Menon", "Iyer",
        "Pillai", "Singh", "Reddy", "Bose", "Chatterjee", "Gupta"]

START = date(2023, 1, 1)
END = date(2024, 12, 31)


def iso(d: date) -> str:
    return d.isoformat()


def build(conn: sqlite3.Connection, n_orders: int) -> None:
    rng = random.Random(SEED)

    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # ---------------------------------------------------------- customers
    customers = []
    # 240 customers, but only ids 1-200 ever place an order. The other 40 are
    # what makes the anti-join in Q2 return something.
    for cid in range(1, 241):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        region = rng.choice(REGIONS)
        signup = START - timedelta(days=rng.randint(0, 400))
        # Roughly a fifth have no credit limit set. This is what makes the
        # NULL-behaviour questions (Q4) interesting rather than academic.
        limit = None if rng.random() < 0.2 else round(rng.uniform(5_000, 250_000), 2)
        customers.append((cid, name, region, iso(signup), limit))
    conn.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers
    )

    # ---------------------------------------------------------- products
    products = []
    for pid in range(1, 41):
        category = CATEGORIES[(pid - 1) % len(CATEGORIES)]
        products.append((pid, f"{category[:-1]} {chr(64 + ((pid - 1) % 26) + 1)}{pid}",
                         category, 1 if pid % 13 == 0 else 0))
    conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    # ------------------------------------------------------ price_history
    # Each product has two or three price periods across the window. A query
    # that joins on product_id alone will multiply rows; a query that uses
    # today's price will silently misprice historical orders. Both are Q11.
    price_rows = []
    for pid, *_ in products:
        base = round(rng.uniform(100, 5_000), 2)
        cuts = sorted(rng.sample(range(60, 700), k=rng.choice([1, 2])))
        boundaries = [START] + [START + timedelta(days=c) for c in cuts] + [date(9999, 12, 31)]
        price = base
        for i in range(len(boundaries) - 1):
            price_rows.append((pid, iso(boundaries[i]), iso(boundaries[i + 1]), round(price, 2)))
            price = price * rng.uniform(1.02, 1.18)
    conn.executemany("INSERT INTO price_history VALUES (?, ?, ?, ?)", price_rows)

    # ---------------------------------------------------------- orders
    # About 4% of orders get a correction row: same order_id, later updated_at,
    # usually a status change. Q7 is deduplicating these correctly.
    span = (END - START).days
    order_rows = []
    item_rows = []
    row_id = 0
    item_id = 0
    for n in range(1, n_orders + 1):
        oid = f"ORD-{n:06d}"
        cid = rng.randint(1, 200)
        odate = START + timedelta(days=rng.randint(0, span))
        status = rng.choices(["placed", "shipped", "cancelled"], weights=[30, 65, 5])[0]
        updated = odate + timedelta(days=rng.randint(0, 3))

        row_id += 1
        order_rows.append((row_id, oid, cid, iso(odate), status, iso(updated)))

        if rng.random() < 0.04:
            row_id += 1
            later = updated + timedelta(days=rng.randint(1, 20))
            corrected = "cancelled" if status != "cancelled" else "shipped"
            order_rows.append((row_id, oid, cid, iso(odate), corrected, iso(later)))

        for _ in range(rng.randint(1, 4)):
            item_id += 1
            item_rows.append((item_id, oid, rng.randint(1, 40), rng.randint(1, 12)))

    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", order_rows)
    conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", item_rows)

    # ---------------------------------------------------------- indexes
    # Deliberately minimal. Q12 asks you to add one and measure the effect,
    # so the index that makes the correlated subquery fast is NOT here.
    conn.executescript(
        """
        CREATE INDEX idx_orders_order_id   ON orders (order_id);
        CREATE INDEX idx_items_order_id    ON order_items (order_id);
        CREATE INDEX idx_price_product     ON price_history (product_id);
        """
    )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Lab 2 sales database.")
    parser.add_argument("--small", action="store_true",
                        help="5,000 orders instead of 50,000, for quick iteration")
    parser.add_argument("--path", type=Path, default=DB_PATH)
    args = parser.parse_args()

    n_orders = 5_000 if args.small else 50_000
    if args.path.exists():
        args.path.unlink()

    with sqlite3.connect(args.path) as conn:
        build(conn, n_orders)
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("customers", "products", "price_history", "orders", "order_items")
        }

    print(f"built {args.path}")
    for table, count in counts.items():
        print(f"  {table:<15} {count:>8,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Seeded sources for Lab A.

Every defect below is DELIBERATE and each one is worth a specific mark in the
rubric. The seeds are generated rather than checked in as files so a candidate
cannot pass by hard-coding around a known row count.

The rule the seeds enforce: a lab that only works on clean data has not been
tested. Each source carries something that will break a naive implementation,
and none of it announces itself.

    python -m laba.seeds generate ./landing
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 41

REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Retail", "SME", "Enterprise"]
CITIES = ["Hyderabad", "Pune", "Chennai", "Delhi", "Kolkata", "Bengaluru", "Mumbai"]
STATUSES = ["placed", "shipped", "delivered", "cancelled"]


# ==========================================================================
# SOURCE 1 — FILE DROP (CSV)
# ==========================================================================
ORDERS_HEADER = ("order_line_id,order_id,customer_id,product_id,quantity,"
                 "unit_price,order_ts,status,updated_at")


def orders_batch(batch: int, rows: int = 2_000) -> list[str]:
    """A day of order lines from the file drop.

    Batch 2 carries a duplicate and a correction. Batch 3 carries a
    late-arriving order dated three weeks earlier.
    """
    rng = random.Random(SEED + batch)
    day = date(2026, 8, 31) + timedelta(days=batch - 1)
    lines: list[str] = []

    for i in range(rows):
        n = batch * 100_000 + i
        order_date = day
        if batch == 3 and i == 0:
            # LATE ARRIVAL. Placed three weeks ago, reaching us today. An
            # extract keyed on the business date would never see it.
            order_date = day - timedelta(days=21)
        quantity = rng.randint(1, 9)
        price = round(rng.uniform(120, 4_800), 2)
        lines.append(
            f"OL-{n:09d},ORD-{n // 3:08d},CUST-{rng.randint(1, 4000):06d},"
            f"PROD-{rng.randint(1, 900):04d},{quantity},{price},"
            f"{order_date} {8 + (i % 12):02d}:00:00,"
            f"{rng.choices(STATUSES, weights=[10, 20, 66, 4])[0]},"
            f"{day} {12 + (i % 8):02d}:00:00")

    if batch == 2:
        # A DUPLICATE of a batch-1 line, with a LATER updated_at. Deduplication
        # must keep this one.
        lines.append("OL-100000000,ORD-33333333,CUST-000001,PROD-0001,4,1000.00,"
                     "2026-08-31 08:00:00,delivered,2026-09-01 19:00:00")
        # A TIE: same key, same updated_at, two rows. This is what breaks rank().
        lines.append("OL-200099998,ORD-66699999,CUST-000002,PROD-0002,2,500.00,"
                     "2026-09-01 09:00:00,shipped,2026-09-01 20:00:00")
        lines.append("OL-200099998,ORD-66699999,CUST-000002,PROD-0002,2,500.00,"
                     "2026-09-01 09:00:00,delivered,2026-09-01 20:00:00")

    return lines


def malformed_batch() -> list[str]:
    """THE malformed file. Lab A must survive this WITHOUT losing the batch.

    Five distinct problems, each one breaking a different naive assumption:

      1. A row with the wrong number of columns
      2. An unescaped comma inside an unquoted field
      3. A non-numeric quantity
      4. An empty price, which is NULL after parsing - the three-valued-logic
         trap, because a naive `price >= 0` on a NULL is NULL, not FALSE
      5. An unparseable timestamp

    A pipeline that fails the whole file scores zero on this criterion. So does
    one that silently drops the file. The rows must be captured and the good
    rows must still land.
    """
    return [
        "OL-999000001,ORD-99900000,CUST-000010,PROD-0010,3",              # short row
        "OL-999000002,ORD-99900001,CUST-000011,PROD-0011,2,1500.00,"
        "2026-09-02 10:00:00,delivered, pending review,2026-09-02 11:00:00",  # extra comma
        "OL-999000003,ORD-99900002,CUST-000012,PROD-0012,N/A,900.00,"
        "2026-09-02 10:00:00,placed,2026-09-02 10:00:00",                 # bad quantity
        "OL-999000004,ORD-99900003,CUST-000013,PROD-0013,1,,"
        "2026-09-02 10:00:00,placed,2026-09-02 10:00:00",                 # empty price
        "OL-999000005,ORD-99900004,CUST-000014,PROD-0014,2,750.00,"
        "not-a-timestamp,placed,2026-09-02 10:00:00",                     # bad timestamp
        # ... and two GOOD rows in the same file. These MUST still land.
        "OL-999000006,ORD-99900005,CUST-000015,PROD-0015,4,1200.00,"
        "2026-09-02 10:00:00,delivered,2026-09-02 10:00:00",
        "OL-999000007,ORD-99900006,CUST-000016,PROD-0016,1,300.00,"
        "2026-09-02 11:00:00,shipped,2026-09-02 11:00:00",
    ]


# ==========================================================================
# SOURCE 2 — DATABASE (SQLite, standing in for Azure SQL)
# ==========================================================================
def build_customer_db(path: Path, *, customers: int = 4_000) -> None:
    """The customer master. Three batches of changes, applied by advance().

    Batch 2 contains customers who change TWICE in one batch. Lab A only has
    to LAND them; what to do about them is a later lab.
    """
    import sqlite3

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY, full_name TEXT, email TEXT,
            city TEXT, region TEXT, segment TEXT, updated_at TEXT NOT NULL);
        CREATE TABLE customer_changes (
            change_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL, customer_id TEXT NOT NULL,
            full_name TEXT, email TEXT, city TEXT, region TEXT, segment TEXT,
            updated_at TEXT NOT NULL);
    """)
    rng = random.Random(SEED)
    base = "2026-08-31 08:00:00"
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)", [
        (f"CUST-{i:06d}", f"Customer {i}", f"user{i}@example.com",
         rng.choice(CITIES), rng.choice(REGIONS), rng.choice(SEGMENTS), base)
        for i in range(1, customers + 1)])

    # Batch 2: 300 customers change; 40 of them change TWICE.
    rng2 = random.Random(SEED + 2)
    changes = []
    for i in range(1, 301):
        code = f"CUST-{i:06d}"
        changes.append((2, code, f"Customer {i}", f"user{i}@example.com",
                        rng2.choice(CITIES), rng2.choice(REGIONS),
                        rng2.choice(SEGMENTS), "2026-09-01 09:00:00"))
        if i <= 40:
            changes.append((2, code, f"Customer {i}", f"user{i}@example.com",
                            rng2.choice(CITIES), rng2.choice(REGIONS),
                            rng2.choice(SEGMENTS), "2026-09-01 16:00:00"))
    # Batch 3: a TYPE 1 change only. Email. Must NOT open a new version.
    for i in range(400, 450):
        changes.append((3, f"CUST-{i:06d}", f"Customer {i}",
                        f"corrected{i}@example.com", None, None, None,
                        "2026-09-02 10:00:00"))

    conn.executemany(
        "INSERT INTO customer_changes (batch_id, customer_id, full_name, email, "
        "city, region, segment, updated_at) VALUES (?,?,?,?,?,?,?,?)", changes)
    conn.commit()
    conn.close()


def advance_customer_db(path: Path, batch: int) -> int:
    """Apply one batch of changes to the source. Returns rows changed.

    Note this mutates the SOURCE. Re-running the PIPELINE must be safe;
    re-applying the SOURCE change must not happen. Conflating those two is why
    "just run it again" frightens people.
    """
    import sqlite3
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT customer_id, full_name, email, city, region, segment, updated_at "
        "FROM customer_changes WHERE batch_id = ? ORDER BY change_id",
        (batch,)).fetchall()
    for r in rows:
        # COALESCE so a Type 1 change carrying only an email does not blank the
        # tracked columns. A candidate whose extract does not handle this will
        # wipe region for 50 customers and open 50 spurious versions.
        conn.execute(
            "UPDATE customers SET full_name = COALESCE(?, full_name), "
            "email = COALESCE(?, email), city = COALESCE(?, city), "
            "region = COALESCE(?, region), segment = COALESCE(?, segment), "
            "updated_at = ? WHERE customer_id = ?",
            (r[1], r[2], r[3], r[4], r[5], r[6], r[0]))
    conn.commit()
    conn.close()
    return len(rows)


# ==========================================================================
# SOURCE 3 — API (paged JSON)
# ==========================================================================
def api_page(page: int, *, page_size: int = 200, total: int = 900) -> dict:
    """One page of a paged API response.

    The API is deliberately awkward in three ways that mirror real ones:

      * `nextPage` is null on the last page, so a loop that trusts a count
        rather than the cursor either stops early or runs for ever.
      * One page repeats a record that appeared on the previous page. Real
        cursor-paged APIs do this when the underlying data shifts mid-read.
      * One record has a null in a required field.
    """
    rng = random.Random(SEED + 100 + page)
    start = page * page_size
    count = min(page_size, total - start)
    records = []
    for i in range(count):
        n = start + i
        record = {
            "productId": f"PROD-{n % 900 + 1:04d}",
            "productName": f"Product {n % 900 + 1}",
            "category": ["Widgets", "Gadgets", "Fittings", "Consumables"][n % 4],
            "listPrice": round(rng.uniform(100, 5_000), 2),
            "discontinued": (n % 37 == 0),
            "updatedAt": "2026-08-31T08:00:00Z",
        }
        if page == 2 and i == 0:
            record["productName"] = None          # required field, null
        records.append(record)

    if page == 3 and records:
        # A record repeated from the previous page. Cursor-paged APIs do this
        # when the underlying data shifts while you are reading it.
        records.insert(0, {
            "productId": "PROD-0401", "productName": "Product 401",
            "category": "Widgets", "listPrice": 1234.56,
            "discontinued": False, "updatedAt": "2026-08-31T08:00:00Z"})

    has_more = start + count < total
    return {
        "page": page,
        "pageSize": page_size,
        "records": records,
        # The cursor is the only reliable signal. There is deliberately no
        # totalCount field to tempt anyone into arithmetic.
        "nextPage": page + 1 if has_more else None,
    }


def write_api_pages(folder: Path, *, total: int = 900) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    page, written = 0, 0
    while True:
        payload = api_page(page, total=total)
        (folder / f"products_page_{page}.json").write_text(
            json.dumps(payload, indent=1), encoding="utf-8")
        written += len(payload["records"])
        if payload["nextPage"] is None:
            return written
        page = payload["nextPage"]


# ==========================================================================
def generate(base: Path) -> dict[str, int]:
    """Lay out all three sources for a clean run."""
    base = Path(base)
    counts: dict[str, int] = {}

    for batch in (1, 2, 3):
        day = date(2026, 8, 31) + timedelta(days=batch - 1)
        folder = base / "filedrop" / "orders" / f"load_date={day}"
        folder.mkdir(parents=True, exist_ok=True)
        lines = orders_batch(batch)
        (folder / f"orders_{day}.csv").write_text(
            "\n".join([ORDERS_HEADER, *lines]) + "\n", encoding="utf-8")
        counts[f"filedrop_batch_{batch}"] = len(lines)

    # The malformed file lands in batch 2's partition, alongside a good file.
    bad_folder = base / "filedrop" / "orders" / "load_date=2026-09-01"
    (bad_folder / "orders_2026-09-01_MALFORMED.csv").write_text(
        "\n".join([ORDERS_HEADER, *malformed_batch()]) + "\n", encoding="utf-8")
    counts["malformed_rows"] = len(malformed_batch())

    build_customer_db(base / "database" / "source.db")
    counts["customers"] = 4_000
    counts["api_records"] = write_api_pages(base / "api" / "products")
    return counts


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] != "generate":
        print(__doc__)
        return 2
    counts = generate(Path(argv[2]))
    print(f"\nseeded {argv[2]}")
    print("-" * 52)
    for name, value in counts.items():
        print(f"  {name:<30}{value:>10,}")
    print("\n  the malformed file sits ALONGSIDE a good file in the same")
    print("  partition. Failing the batch loses both.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

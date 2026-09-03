# Source contracts

Sample CSVs are in place. IDs are shared across sources so silver joins produce a connected fact table. A few dirty rows are intentional for silver quality rules.

## ADLS Gen2 — `orders` (`data/adls/orders.csv`)

| Column | Type (logical) | Notes |
|---|---|---|
| order_id | string | PK |
| customer_id | string | FK → customers |
| order_date | date / mixed string | mostly `yyyy-MM-dd`; O010 uses `MM/dd/yyyy` |
| order_status | string | completed, pending, cancelled (O013 has `Completed`) |
| total_amount | decimal | |

**Bronze:** `bronze.orders` · `source_system = adls`  
**Rows:** 13

**Intentional issues:** `C999` orphan customer (O009); mixed date format (O010); mixed status casing (O013).

## ADLS Gen2 — `order_items` (`data/adls/order_items.csv`)

| Column | Type (logical) | Notes |
|---|---|---|
| order_item_id | string | PK |
| order_id | string | FK → orders |
| product_id | string | FK → products |
| quantity | int | |
| unit_price | decimal | |
| line_total | decimal | |

**Bronze:** `bronze.order_items` · `source_system = adls`  
**Rows:** 19

**Intentional issues:** `P999` orphan product (OI013); duplicate line OI015 ≈ OI001 (same order/product).

## Google Drive — `products` (`data/google_drive/products.csv`)

| Column | Type (logical) | Notes |
|---|---|---|
| product_id | string | PK |
| product_name | string | may have leading/trailing spaces |
| category | string | mixed case (`electronics` / `Furniture` / `ELECTRONICS`) |
| unit_price | decimal | |
| stock_qty | int | P008 blank → treat as null |

**Bronze:** `bronze.products` · `source_system = google_drive`  
**Rows:** 10

## Confluence — `customers` (`data/confluence/customers.csv`)

| Column | Type (logical) | Notes |
|---|---|---|
| customer_id | string | PK |
| first_name | string | may have spaces (C009) |
| last_name | string | |
| email | string | C006 blank; C009 needs lower/trim |
| country | string | mixed case / spaces (C009) |
| signup_date | date | |

**Bronze:** `bronze.customers` · `source_system = confluence`  
**Rows:** 10

**Intentional issues:** duplicate logical customer C007 ≈ C001 (same email); blank email on C006.

## Join graph

```text
customers.customer_id = orders.customer_id
orders.order_id       = order_items.order_id
products.product_id   = order_items.product_id
```

### Valid connection examples

| Order | Customer (Confluence) | Products (Drive) |
|---|---|---|
| O001 | C001 John Smith | P001 Laptop, P002 Mouse |
| O011 | C009 Frank Miller | P009 Standing Desk |
| O012 | C010 Grace Lee | P010 Headphones |

### Expected silver drop / filter examples

| Row | Why |
|---|---|
| O009 / OI013 | orphan `C999` / `P999` |
| OI015 | duplicate of OI001 after dedupe strategy |
| C007 | duplicate `customer_id` or same email as C001 (policy choice in silver) |

# Build a sample data pipeline

Multi-source medallion pipeline on Azure Databricks: **ADLS Gen2**, **Google Drive**, and **Confluence** → bronze → silver → gold.

No Autoloader. No Azure SQL. Notebooks are `.ipynb` for import and cell-by-cell runs in the Databricks workspace.

## Sources and how data connects

| Source | Seed path | Bronze table | Role |
|---|---|---|---|
| ADLS Gen2 | `data/adls/` | `orders`, `order_items` | Transactional OMS dump |
| Google Drive | `data/google_drive/` | `products` | Merchandising product catalog |
| Confluence | `data/confluence/` | `customers` | Ops customer registry |

Join keys: `customer_id`, `order_id`, `product_id`.

```text
Confluence.customers ──< ADLS.orders ──< ADLS.order_items >── GoogleDrive.products
```

## Notebook order

1. `notebooks/00_setup_uc_and_paths.ipynb` — catalog, schemas, paths, secrets check  
2. `notebooks/01_bronze_ingest.ipynb` — ingest three sources into bronze  
3. `notebooks/02_silver_transform.ipynb` — clean, dedupe, FK joins, enriched fact  
4. `notebooks/03_gold_aggregate.ipynb` — aggregates / KPIs  

Wire as a Databricks Job: `00` → `01` → `02` → `03` (or start from `01` if setup is already done).

## Layout

```text
Build a sample data pipeline/
  data/adls|google_drive|confluence/   sample / seed files
  notebooks/                           Databricks notebooks (.ipynb)
  queries/                             dashboard / validation SQL
  docs/                                architecture, source contracts, CHECKPOINT
  completion_screenshots/              job / dashboard evidence
```

**Resume elsewhere:** read `docs/CHECKPOINT.md` and continue from the Next action section.

## Sample data (Step 2)

| File | Rows | Notes |
|---|---|---|
| `data/confluence/customers.csv` | 10 | Includes blank email, duplicate John Smith, messy C009 |
| `data/google_drive/products.csv` | 10 | Mixed category casing; blank `stock_qty` on P008 |
| `data/adls/orders.csv` | 13 | Orphan `C999`; mixed date/status formats |
| `data/adls/order_items.csv` | 19 | Orphan `P999`; duplicate line OI015 |

See `docs/source_contracts.md` for full column contracts and join examples.

## Status

- [x] Step 1 — folder skeleton  
- [x] Step 2 — connected sample CSVs  
- [x] Step 3 — setup notebook (`notebooks/00_setup_uc_and_paths.ipynb`)  
- [ ] Step 4 — bronze ingest  
- [ ] Step 5 — silver transform  
- [ ] Step 6 — gold aggregate  
- [ ] Step 7 — queries + job wiring  

# Session checkpoint — Build a sample data pipeline

**Last updated:** 2026-09-03  
**Project path:** `Week4/Build a sample data pipeline/`  
**Resume prompt:** Open this file and say: *Continue from Step 4 using docs/CHECKPOINT.md*

---

## Goal (locked decisions)

Build a **multi-source medallion pipeline** in Azure Databricks, structurally similar to `Week4/Autoloader Ingestion/`, with these constraints:

| Decision | Choice |
|---|---|
| Layers | bronze → silver → gold |
| Autoloader | **No** — batch ingest only |
| Azure SQL | **No** — previous gateway issues from Databricks |
| Sources (3) | **ADLS Gen2**, **Google Drive**, **Confluence** |
| Notebook format | **`.ipynb`** (importable / runnable in Databricks workspace) |
| Data | Custom sample CSVs; must be **connected** via shared keys |
| Catalog name | `sample_pipeline` |
| Storage pattern | Same as Autoloader: `stpracticeecom` / `practice-ecommerce` (editable in setup Config) |

### Domain ownership

| Source | Owns | Seed path | Bronze table(s) | `source_system` |
|---|---|---|---|---|
| ADLS Gen2 | Transactions | `data/adls/` | `orders`, `order_items` | `adls` |
| Google Drive | Product catalog | `data/google_drive/` | `products` | `google_drive` |
| Confluence | Customer registry | `data/confluence/` | `customers` | `confluence` |

### Join graph

```text
Confluence.customers ──< ADLS.orders ──< ADLS.order_items >── GoogleDrive.products
         customer_id              order_id / product_id              product_id
```

Silver builds `order_lines_enriched`; gold aggregates (e.g. `daily_sales_summary` for completed orders) — mirror Autoloader silver/gold logic.

### Ingest strategy (agreed)

- Prefer **live API** for Drive / Confluence when cluster has network + secrets.
- Always support **ADLS-landed seed CSVs** as fallback (upload from `data/`).
- Setup notebook creates landing dirs under:
  `abfss://practice-ecommerce@stpracticeecom.dfs.core.windows.net/landing/sample_pipeline/`

---

## Step plan

| Step | Deliverable | Status |
|---|---|---|
| 1 | Folder skeleton + README + docs stubs | **Done** |
| 2 | Connected sample CSVs under `data/` | **Done** |
| 3 | `notebooks/00_setup_uc_and_paths.ipynb` | **Done** |
| 4 | `notebooks/01_bronze_ingest.ipynb` | **Next** |
| 5 | `notebooks/02_silver_transform.ipynb` | Pending |
| 6 | `notebooks/03_gold_aggregate.ipynb` | Pending |
| 7 | `queries/` SQL + Databricks Job wiring notes | Pending |

**Do one step at a time; wait for user confirmation before advancing.**

---

## What exists on disk now

```text
Week4/Build a sample data pipeline/
  README.md
  docs/
    architecture.md
    source_contracts.md
    CHECKPOINT.md              ← this file
  data/
    adls/orders.csv            (13 rows)
    adls/order_items.csv       (19 rows)
    google_drive/products.csv  (10 rows)
    confluence/customers.csv   (10 rows)
  notebooks/
    00_setup_uc_and_paths.ipynb
  queries/                     (.gitkeep only)
  completion_screenshots/      (.gitkeep only)
```

### Reference projects in this repo

- `Week4/Autoloader Ingestion/` — silver/gold patterns to reuse (`02_silver_transform.py`, `03_gold_aggregate.py`); bronze used Autoloader — **do not copy** that for bronze.
- `Week3/Lab 8 — bronze and silver in Unity Catalog/` — UC catalog/schema/grants thinking.
- Avoid Azure SQL (Week2 enterprise integration used SQL; not for this project).

---

## Setup notebook summary (`00`)

Already created. Key constants:

- `CATALOG = "sample_pipeline"`
- Schemas: `bronze`, `silver`, `gold`
- Landing paths under `.../landing/sample_pipeline/{adls|google_drive|confluence}/...`
- `SECRET_SCOPE = "sample_pipeline"`
- Optional secrets (probe only; seed-file bronze works without them):
  - `confluence_base_url`, `confluence_email`, `confluence_api_token`
  - `google_drive_file_id`

User must: import `.ipynb` → edit storage names if needed → run → upload four CSVs to ADLS landing (or set `SEED_ROOT` and copy).

---

## Intentional dirty rows (for silver)

| Issue | Where |
|---|---|
| Orphan customer `C999` | `orders` O009 |
| Orphan product `P999` | `order_items` OI013 |
| Duplicate line | OI015 ≈ OI001 |
| Duplicate customer identity | C007 ≈ C001 (same email) |
| Blank email | C006 |
| Mixed date format | O010 `07/25/2024` |
| Mixed status casing | O013 `Completed` |
| Blank `stock_qty` | P008 |
| Messy trim/case | C009, product names/categories |

Full contracts: `docs/source_contracts.md`.

---

## Next action — Step 4

Create `notebooks/01_bronze_ingest.ipynb` that:

1. Reuses the same Config constants as `00`.
2. Batch-reads **ADLS** → `sample_pipeline.bronze.orders` and `order_items` with `ingestion_ts`, `source_system='adls'`.
3. Ingests **Google Drive** products:
   - Primary: read landed CSV from `LANDING_DRIVE_PRODUCTS` (and/or optional API download into `_stage/` then read).
   - Tag `source_system='google_drive'`.
4. Ingests **Confluence** customers:
   - Primary: read landed CSV from `LANDING_CONFLUENCE_CUSTOMERS` (and/or optional REST download).
   - Tag `source_system='confluence'`.
5. Verification cell: row counts per bronze table.
6. Mode: `overwrite` is fine for the lab.

Do **not** start Steps 5–7 until Step 4 is confirmed done.

---

## How to resume on another device

1. Pull/sync this git repo.
2. Open `Week4/Build a sample data pipeline/docs/CHECKPOINT.md`.
3. In Cursor, ask: **Continue Step 4 from docs/CHECKPOINT.md** (Agent mode).
4. After each step, update the Status table in this file and in `README.md`.

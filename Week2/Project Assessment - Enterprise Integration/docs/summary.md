# Enterprise Carts Ingestion — Peer Summary & Data Simulation

**Project:** Azure Enterprise Integration Pipeline  
**Pipeline:** `pl_ingest_carts`  
**Simulation object:** `carts_page_001.json` (DummyJSON carts page)  
**Goal:** Explain architecture, services, naming, and the full data lifecycle using the real file we landed in ADLS.

---

## 1. Elevator pitch

We built an Azure Data Factory pipeline that:

1. Reads a checkpoint from a SQL watermark table  
2. Pulls shopping-cart JSON from the DummyJSON REST API  
3. Lands the payload unchanged in ADLS Gen2 (`raw`)  
4. Flattens nested `carts[]` / `products[]` into SQL staging  
5. MERGEs into a curated table (idempotent upsert)  
6. Updates the watermark **only after full success**

Everything is secured with Managed Identity and versioned in GitHub under `Week2/enterprise_integration/`.

---

## 2. Architecture overview

```text
DummyJSON REST API  (/carts?limit=10&skip=0)
        │
        │  ADF Copy activity
        ▼
ADLS Gen2  raw/api/dummyjson/carts/carts_page_001.json     ← RAW (bronze)
        │
        │  Mapping Data Flow (df_flatten_carts)
        ▼
Azure SQL  dbo.stg_CartProducts                            ← STAGING
        │
        │  usp_MergeCartProducts (MERGE)
        ▼
Azure SQL  dbo.CartProducts                                ← CURATED
        │
        │  usp_UpdateWatermark (on success only)
        ▼
Azure SQL  dbo.ETL_Watermark                               ← CONTROL
        │
        ▼
Azure SQL  dbo.vw_CartProductSummary                       ← REPORTING
```

**Pipeline order (must succeed in sequence):**

```text
GetWatermark → Copy_Carts_To_Raw → FlattenAndLoad → MergeToCurated → UpdateWatermark
```

---

## 3. Azure services used (what each does)

| Service | Role in this project |
|---|---|
| **Azure Data Factory (ADF)** | Orchestrates the pipeline: order, retries, monitoring, connectors |
| **ADLS Gen2** | Data lake for raw JSON landing (hierarchical folders/files) |
| **Azure SQL Database** | Staging, curated tables, watermark control, reporting view |
| **Managed Identity** | Secretless auth from ADF → Storage and SQL |
| **GitHub + ADF Git** | Versions pipeline/dataset/dataflow JSON + SQL scripts |
| **DummyJSON** | Public anonymous REST source (stands in for a real enterprise API) |

### ADF building blocks

| Concept | Prefix / example | Meaning |
|---|---|---|
| Pipeline | `pl_ingest_carts` | End-to-end workflow |
| Linked service | `LS_*` | Connection + auth to a system |
| Dataset | `DS_*` | Specific table/path/resource |
| Data flow | `df_*` | Visual Spark transform |
| Activity | Lookup / Copy / Execute Data Flow / Stored Proc | One pipeline step |

**Linked services we used**

- `LS_REST_DummyJSON` → `https://dummyjson.com/`
- `LS_ADLS_Raw` → storage account (Managed Identity)
- `LS_AzureSQL` → `sqldb-carts` (Managed Identity)

---

## 4. Naming conventions

| Pattern | Meaning | Examples |
|---|---|---|
| `pl_*` | Pipeline | `pl_ingest_carts` |
| `LS_*` | Linked service | `LS_REST_DummyJSON` |
| `DS_*` | Dataset | `DS_REST_Carts`, `DS_ADLS_Raw_JSON` |
| `df_*` | Data flow | `df_flatten_carts` |
| `stg_*` | Staging table | `stg_CartProducts` |
| `usp_*` | Stored procedure | `usp_MergeCartProducts` |
| `vw_*` | View | `vw_CartProductSummary` |
| `ETL_*` | Control / ops metadata | `ETL_Watermark` |

**Lake path convention**

```text
raw / api / dummyjson / carts / carts_page_001.json
 │     │       │          │            │
 │     │       │          │            └─ page file name
 │     │       │          └─ entity
 │     │       └─ source system
 │     └─ source type
 └─ layer (raw container)
```

---

## 5. Simulation object: `carts_page_001.json`

### How the file is produced

- **HTTP:** `GET https://dummyjson.com/carts?limit=10&skip=0`
- **ADF source dataset:** `DS_REST_Carts` (`relativeUrl = carts?limit=10&skip=0`)
- **ADF sink dataset:** `DS_ADLS_Raw_JSON`
  - filesystem: `raw`
  - folder: `api/dummyjson/carts`
  - file: `carts_page_001.json`

### What’s inside (summary)

| Property | Value |
|---|---|
| Carts on this page | **10** (`id` 1–10) |
| API `total` | 208 carts available overall |
| `skip` / `limit` | 0 / 10 |
| Product lines after flatten | **39** (sum of nested products) |

### Example nested shape (Cart 1, first product)

```json
{
  "id": 1,
  "userId": 1,
  "total": 13037.88,
  "products": [
    {
      "id": 162,
      "title": "Blue Frock",
      "price": 29.99,
      "quantity": 4,
      "total": 119.96
    }
  ]
}
```

This nested product becomes **one SQL row** after flatten.

---

## 6. Point-to-point lifecycle (follow the file)

### T0 — `GetWatermark` (Lookup)

| Item | Detail |
|---|---|
| **Purpose** | Read last successful checkpoint before extract |
| **Dataset** | `DS_SQL_ETL_Watermark` → `dbo.ETL_Watermark` |
| **Linked service** | `LS_AzureSQL` |
| **Query** | `SELECT WatermarkValue FROM dbo.ETL_Watermark WHERE SourceSystem='DummyJSON' AND EntityName='Carts'` |
| **First row only** | ON |
| **Parameters** | none |
| **Touches JSON file?** | No |

**Example output**

```text
firstRow.WatermarkValue = "0"
```

**Why it exists:** Control-table pattern for incremental loads. DummyJSON has no true `updated_after` filter, so watermark is largely a success marker in this lab.

---

### T1 — `Copy_Carts_To_Raw` (Copy) — file is created

| Item | Detail |
|---|---|
| **Purpose** | Land API payload unchanged in the lake |
| **Depends on** | `GetWatermark` Succeeded |
| **Source** | `DS_REST_Carts` + `LS_REST_DummyJSON` |
| **Sink** | `DS_ADLS_Raw_JSON` + `LS_ADLS_Raw` |
| **Output path** | `raw/api/dummyjson/carts/carts_page_001.json` |
| **Transform?** | None — raw fidelity |

**Input:** HTTP JSON from DummyJSON  
**Output:** Same JSON as our simulation file in ADLS  

**Teaching point:** Raw layer = audit / reprocess / unchanged source copy.

---

### T2 — `FlattenAndLoad` (Execute Data Flow `df_flatten_carts`)

| Item | Detail |
|---|---|
| **Purpose** | Nested JSON → flat product-line rows → staging |
| **Depends on** | `Copy_Carts_To_Raw` Succeeded |
| **Data flow** | `df_flatten_carts` |
| **Source dataset** | ADLS folder dataset under `raw/api/dummyjson/carts` |
| **Sink dataset** | `DS_SQL_stg_CartProducts` → `dbo.stg_CartProducts` |
| **Sink mode** | Truncate table, then insert |
| **Compute** | General, 8 cores |

#### Transform streams

1. **RawCarts** — read JSON document  
2. **FlattenCarts** — unroll `carts[]` → 10 cart rows  
3. **FlattenProducts** — unroll `products[]` → 39 product-line rows  
4. **MapColumns** — rename/cast to staging schema  
5. **SinkStaging** — truncate + load `stg_CartProducts`

#### Field mapping (Cart 1 / Blue Frock)

| Staging column | Expression | Example value |
|---|---|---|
| `cart_id` | `id` | `1` |
| `user_id` | `userId` | `1` |
| `product_id` | `products.id` | `162` |
| `product_title` | `products.title` | `Blue Frock` |
| `quantity` | `toInteger(products.quantity)` | `4` |
| `price` | `toDecimal(products.price, 18, 4)` | `29.9900` |
| `line_total` | `toDecimal(products.total, 18, 4)` | `119.9600` |
| `cart_total` | `toDecimal(total, 18, 4)` | `13037.8800` |
| `ingest_ts` | `currentUTC()` | run timestamp |
| `source_file` | `''` | empty in current flow |

#### Grain change

```text
File grain:  1 JSON document → 10 nested carts
SQL grain:   1 row = 1 (cart_id, product_id) product line
```

**Expected staging rows from this file:** ~**39**

Sample staging (Cart 1):

| cart_id | product_id | product_title | quantity | line_total | cart_total |
|---|---|---|---|---|---|
| 1 | 162 | Blue Frock | 4 | 119.96 | 13037.88 |
| 1 | 113 | Generic Motorcycle | 3 | 11999.97 | 13037.88 |
| 1 | 122 | iPhone 6 | 3 | 899.97 | 13037.88 |
| 1 | 138 | Baseball Ball | 2 | 17.98 | 13037.88 |

**Note:** The lake file remains unchanged; staging is a relational projection of it.

---

### T3 — `MergeToCurated` (`usp_MergeCartProducts`)

| Item | Detail |
|---|---|
| **Purpose** | Upsert staging into durable curated table |
| **Depends on** | `FlattenAndLoad` Succeeded |
| **Proc** | `[dbo].[usp_MergeCartProducts]` |
| **Linked service** | `LS_AzureSQL` |
| **Parameters** | none |
| **Match key** | `(cart_id, product_id)` |

**Behavior**

- Key exists → **UPDATE**  
- Key new → **INSERT**

**Curated extras vs staging**

- `last_updated` (from staging ingest time)  
- `is_active` (default 1)  
- Primary key on `(cart_id, product_id)`

**Idempotency:** Re-running with the same file updates the same ~39 keys; it does **not** double to 78 rows.

**Does MERGE read the JSON file?** No — only `stg_CartProducts`.

---

### T4 — `UpdateWatermark` (`usp_UpdateWatermark`)

| Item | Detail |
|---|---|
| **Purpose** | Advance checkpoint only after full success |
| **Depends on** | `MergeToCurated` Succeeded |
| **Proc** | `[dbo].[usp_UpdateWatermark]` |

**ADF stored-procedure parameters (names without `@`)**

| Name | Type | Value | Meaning |
|---|---|---|---|
| `SourceSystem` | String | `DummyJSON` | source system |
| `EntityName` | String | `Carts` | entity |
| `NewWatermark` | String | `@utcnow()` | simulated watermark |

**Before run**

```text
WatermarkValue = '0'
```

**After successful run**

```text
WatermarkValue = <UTC timestamp>
Status         = Success
LastRunUtc     = <now>
```

**Failure rule:** If Copy / Flatten / Merge fails, this step does not run — watermark stays unchanged.

> ADF gotcha: parameter **names** must be `SourceSystem` (not `@SourceSystem`). A leading `@` in the name is treated as an expression and causes `InvalidTemplate: Unable to parse expression 'SourceSystem'`.

---

### T5 — Reporting (`vw_CartProductSummary`)

Not an ADF activity. Query curated data:

```sql
SELECT TOP 20 * FROM dbo.vw_CartProductSummary ORDER BY revenue DESC;
```

**Cart 1 example (4 lines, quantities 4+3+3+2 = 12)**

| cart_id | user_id | product_lines | total_units | revenue |
|---|---|---|---|---|
| 1 | 1 | 4 | 12 | 13037.88 |

Revenue matches cart-level `total` in the JSON for cart 1.

---

## 7. SQL objects (layer roles)

| Object | Layer | Role |
|---|---|---|
| `ETL_Watermark` | Control | Last successful run checkpoint |
| `stg_CartProducts` | Staging | Truncate/load batch for current run |
| `CartProducts` | Curated | Durable upserted product lines |
| `usp_MergeCartProducts` | Load logic | MERGE staging → curated |
| `usp_UpdateWatermark` | Control logic | Update watermark on success |
| `vw_CartProductSummary` | Serve | Aggregates for reporting |

---

## 8. Inputs / outputs cheat sheet

| Step | Inputs | Outputs |
|---|---|---|
| GetWatermark | `ETL_Watermark` | `WatermarkValue` in activity output |
| Copy_Carts_To_Raw | REST `carts?limit=10&skip=0` | `carts_page_001.json` in ADLS |
| FlattenAndLoad | That ADLS file/folder | ~39 rows in `stg_CartProducts` |
| MergeToCurated | Staging rows | Upserted `CartProducts` |
| UpdateWatermark | DummyJSON / Carts / `@utcnow()` | Updated watermark row |
| Reporting view | `CartProducts` | Cart-level aggregates |

---

## 9. What this design does *not* use (yet)

Current pipeline has:

- No pipeline parameters / variables  
- Hardcoded `limit=10&skip=0`  
- Hardcoded sink file `carts_page_001.json`  
- Watermark write does not consume `GetWatermark` for API skip (simulated only)

Optional later upgrades: Until-loop pagination, dynamic file names, Key Vault/OAuth for real APIs, schedule trigger (concurrency = 1).

---

## 10. How we prove success

```sql
SELECT * FROM dbo.ETL_Watermark
WHERE SourceSystem = 'DummyJSON' AND EntityName = 'Carts';

SELECT COUNT(*) AS staging_rows FROM dbo.stg_CartProducts;
SELECT COUNT(*) AS curated_rows FROM dbo.CartProducts;

SELECT TOP 20 * FROM dbo.vw_CartProductSummary
ORDER BY revenue DESC;
```

Also verify in Storage Explorer / Portal:

```text
raw/api/dummyjson/carts/carts_page_001.json
```

And ADF Output: all five activities **Succeeded**.

---

## 11. Security model (short)

```text
ADF System-Assigned Managed Identity
   ├─ ADLS: Storage Blob Data Contributor
   └─ Azure SQL: AAD user + read/write/execute
```

DummyJSON is anonymous. No storage keys or SQL passwords in Git.

---

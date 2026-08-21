# Project 1 — Enterprise Integration Pipeline

**Execution Runbook (2-Hour Delivery)**

| Field | Value |
|---|---|
| **Pipeline** | REST API → Azure Data Factory → ADLS Gen2 → Azure SQL DB → Reporting |
| **Document Version** | 1.1 |
| **Last Updated** | August 2026 |
| **Source of Truth** | `Project1_Enterprise_Integration_Pipeline_Implementation.docx` |
| **Implementation Source** | DummyJSON REST API (`/carts`) |
| **Source Control** | GitHub + Azure Data Factory Git integration |
| **Timebox** | **2 hours** end-to-end |
| **Development Model** | Azure Portal / ADF Studio for Azure artifacts; VS Code for Git, SQL, docs |

---

## Implementation Rules

This runbook executes the **DOCX architecture** as a **Git-controlled Azure project**. The external API placeholder is replaced with **DummyJSON `/carts`** for a learning implementation.

- Build Azure resources in the **Azure Portal**.
- Build ADF pipelines, datasets, linked services, data flows, and triggers in **ADF Studio**.
- Connect ADF Studio to **GitHub before creating project artifacts**.
- Use **VS Code** for Git, SQL scripts, and documentation.
- Do **not** replace the DOCX layers with a simplified pipeline — implement the same sequence, thinned for the timebox.
- Do **not** start CI/CD or Bicep in the 2-hour window. Git control first; automation later.
- **DummyJSON specifics:** Anonymous auth + `limit`/`skip` pagination only. OAuth2 and cursor pagination remain DOCX reference patterns — do not invent DummyJSON fields or behavior.

### Work split (2-hour reality)

| Where | Share | What |
|---|---|---|
| **Azure Portal + ADF Studio** | ~75–80% | Resources, linked services, pipeline, data flow, triggers |
| **VS Code + Git** | ~20–25% | Repo, SQL scripts, commits, docs |

### Git Repository

```text
azure-enterprise-integration-pipeline/
├── README.md
├── docs/
│   └── architecture.md
├── sql/
│   ├── 01_control_tables.sql
│   ├── 02_staging_tables.sql
│   ├── 03_curated_tables.sql
│   ├── 04_stored_procedures.sql
│   └── 05_reporting_views.sql
├── infrastructure/          # optional — after 2-hour delivery
│   └── bicep/
└── adf/                     # populated by ADF Git integration
    ├── pipelines/
    ├── datasets/
    ├── linkedServices/
    ├── dataflows/
    └── triggers/
```

Use branch `dev/project-1` (or ADF collaboration branch). Merge to `main` only after a successful end-to-end run.

---

## Table of Contents

1. [2-Hour Milestone Plan](#1-2-hour-milestone-plan)
2. [Executive Summary](#2-executive-summary)
3. [Prerequisites & Azure Resources](#3-prerequisites--azure-resources)
4. [Source API — DummyJSON](#4-source-api--dummyjson)
5. [Milestone Details](#5-milestone-details)
6. [DOCX Reference Patterns (Do Not Build in 2 Hours)](#6-docx-reference-patterns-do-not-build-in-2-hours)
7. [Validation & Definition of Done](#7-validation--definition-of-done)
8. [Best Practices](#8-best-practices)
9. [Appendix](#9-appendix)

---

## 1. 2-Hour Milestone Plan

Execute in order. If behind schedule, use the **simplify** column.

| Clock | Milestone | Focus | Where | Simplify if behind |
|---|---|---|---|---|
| **0:00–0:20** | **M0 — Foundations** | RG, ADF, ADLS, Azure SQL, MI + RBAC, `raw`/`curated`, GitHub repo, **ADF → Git** | Portal + GitHub + VS Code | Drop Key Vault for now |
| **0:20–0:35** | **M1 — Connectivity** | Linked services: REST (Anonymous), ADLS, Azure SQL; test connections | ADF Studio | Skip Key Vault linked service |
| **0:35–0:55** | **M2 — SQL layer** | Watermark, staging, curated, MERGE + watermark procs, 1 view, seed row | VS Code → Azure SQL | Drop `ETL_ErrorLog` and extra views |
| **0:55–1:20** | **M3 — Extract + pagination** | Copy/Web → ADLS raw; DummyJSON `limit`/`skip` (2–3 pages) | ADF Studio | Single-page extract only |
| **1:20–1:40** | **M4 — Flatten → staging** | Mapping Data Flow Flatten `products[]` → staging | ADF Studio | Copy JSON path mapping if Data Flow stuck |
| **1:40–1:55** | **M5 — MERGE + watermark** | Lookup watermark → Data Flow → MERGE → Update watermark on success | ADF Studio | Skip MERGE; prove raw + staging only |
| **1:55–2:00** | **M6 — Prove + Git** | Full manual run; verify lake + SQL + watermark; commit/push | ADF + VS Code | Skip schedule trigger |

### Must-hit vs defer

**Must hit (DOCX core in 2 hours)**

- REST → ADF → ADLS raw → Flatten → SQL staging → MERGE curated → watermark control table → Git-backed ADF

**Defer (after the 2-hour delivery)**

- OAuth2 Web activity, API-key auth against DummyJSON
- Cursor-based pagination
- Dead-letter folder, Logic App / Teams notifications
- Schedule/tumbling trigger polish, Log Analytics deep dive
- Bicep / ARM, GitHub Actions CI/CD
- True source-side `updated_at` incremental filter

### Checkpoint rules

| Clock | If not done… |
|---|---|
| **0:20** | Drop Key Vault; Anonymous + Managed Identity only |
| **0:55** | Watermark + staging + curated + MERGE only (no error log) |
| **1:20** | Single-page extract; no Until loop |
| **1:40** | Prefer Copy mapping over Data Flow |
| **1:55** | Document curated MERGE as follow-up if unfinished |

---

## 2. Executive Summary

Build a production-shaped enterprise data integration pipeline that:

- Extracts JSON from an external REST API (DummyJSON `/carts`)
- Lands raw JSON in **ADLS Gen2**
- Flattens nested arrays with **Mapping Data Flow**
- Loads **Azure SQL** staging → curated via **MERGE**
- Tracks progress with an **ETL watermark** control table
- Versions everything via **ADF Git + GitHub**

### 2.1 Solution Scope

| Layer | Technology | 2-hour notes |
|---|---|---|
| **Source** | DummyJSON `/carts` | Nested `products[]` for Flatten practice |
| **Orchestration** | Azure Data Factory | One pipeline: `pl_ingest_carts` |
| **Landing zone** | ADLS Gen2 | `raw` required; `curated` Parquet optional |
| **Serving layer** | Azure SQL Database | Staging + curated + MERGE |
| **Reporting** | SQL view(s) | One view minimum |
| **Cross-cutting** | MI, watermark, retries if time | OAuth/cursor = reference only |

### 2.2 High-Level Architecture

```text
DummyJSON /carts
      │
      ▼
ADF (Copy / Until + limit/skip)
      │
      ▼
ADLS Gen2 (raw JSON)
      │
      ▼
Mapping Data Flow (Flatten products[])
      │
      ▼
Azure SQL (staging → MERGE → curated)
      │
      ▼
Reporting view(s)
```

---

## 3. Prerequisites & Azure Resources

### 3.1 Azure Resources Checklist

- [ ] **Azure Data Factory V2** — Managed Identity ON
- [ ] **ADLS Gen2** — Hierarchical namespace ON
- [ ] **Azure SQL Database** — ADF MI can read/write
- [ ] **Azure Key Vault** — optional in 2-hour run; required for full DOCX parity later
- [ ] **Log Analytics** — optional if time remains

| Resource | Purpose | Auth |
|---|---|---|
| Azure Data Factory V2 | Orchestration | System-assigned MI |
| ADLS Gen2 | Raw (+ curated) landing | MI → Storage Blob Data Contributor |
| Azure SQL Database | Staging + curated + control | MI → db access |
| Key Vault | Secrets (later / DOCX) | MI get/list |

### 3.2 ADLS Folder Layout

```text
abfss://raw@<storage>.dfs.core.windows.net/
  api/dummyjson/carts/yyyy/MM/dd/HH/
    carts_page_001.json
    carts_page_002.json

abfss://curated@<storage>.dfs.core.windows.net/   # optional in 2 hours
  api/dummyjson/carts/yyyy/MM/dd/
    data.parquet
```

- [ ] Create `raw` container
- [ ] Create `curated` container
- [ ] Grant ADF MI **Storage Blob Data Contributor**

---

## 4. Source API — DummyJSON

### 4.1 Endpoints

```text
https://dummyjson.com/carts
https://dummyjson.com/carts?limit=10&skip=0
```

Use small pages (`limit=10`) so pagination finishes inside the timebox.

### 4.2 Scope note (important)

| DOCX concept | DummyJSON reality | 2-hour action |
|---|---|---|
| API Key / OAuth2 | Not required | Use **Anonymous** |
| Cursor pagination | Not provided | Use **`limit` + `skip`** |
| `updated_at` watermark filter | Not provided | Build control table + update-on-success; label as **simulated** |
| Nested JSON | `products[]` available | Flatten in Mapping Data Flow |

Do not fabricate `updated_at`, OAuth tokens, or cursor fields.

### 4.3 Source-to-project mapping

```text
DummyJSON /carts
  → LS_REST_DummyJSON (Anonymous)
  → Copy / Until (limit + skip)
  → ADLS raw JSON
  → df_flatten_carts (Flatten products[])
  → dbo.stg_CartProducts
  → usp_MergeCartProducts
  → dbo.CartProducts
  → reporting view
  → usp_UpdateWatermark (on success only)
```

---

## 5. Milestone Details

### 5.1 M0 — Foundations (0:00–0:20)

**Where:** Azure Portal, GitHub, VS Code

1. Create GitHub repository; clone locally; add folder skeleton (`docs/`, `sql/`).
2. Create Resource Group.
3. Create ADF, ADLS Gen2 (HNS ON), Azure SQL Database.
4. Enable ADF Managed Identity; grant Storage + SQL permissions.
5. Create `raw` and `curated` containers.
6. In ADF Studio: **Set up Code Repository** → GitHub **before** creating pipelines.
7. Commit initial README; push.

**Exit:** Resources live; ADF Git-connected; repo pushed.

---

### 5.2 M1 — Connectivity (0:20–0:35)

**Where:** ADF Studio

| Linked Service | Type | Auth |
|---|---|---|
| `LS_REST_DummyJSON` | RestService | **Anonymous** — `https://dummyjson.com/` |
| `LS_ADLS_Raw` | AzureBlobFS | Managed Identity |
| `LS_AzureSQL` | AzureSqlDatabase | Managed Identity |
| `LS_KeyVault` | AzureKeyVault | Managed Identity (optional) |

```json
{
  "name": "LS_REST_DummyJSON",
  "type": "Microsoft.DataFactory/factories/linkedservices",
  "properties": {
    "type": "RestService",
    "typeProperties": {
      "url": "https://dummyjson.com/",
      "enableServerCertificateValidation": true,
      "authenticationType": "Anonymous"
    }
  }
}
```

- [ ] Test every linked service connection
- [ ] Confirm ADF Git saved linked service JSON

**Exit:** All required connections succeed.

---

### 5.3 M2 — SQL layer (0:35–0:55)

**Where:** VS Code (author) → Azure SQL (execute) → Git (commit)

Align columns to DummyJSON carts/products (not DOCX “orders” names).

#### Control table + seed

```sql
CREATE TABLE dbo.ETL_Watermark (
    SourceSystem   NVARCHAR(100)  NOT NULL,
    EntityName     NVARCHAR(100)  NOT NULL,
    WatermarkValue NVARCHAR(100)  NOT NULL,
    LastRunUtc     DATETIME2(3)   NOT NULL,
    RowsExtracted  BIGINT         NULL,
    Status         NVARCHAR(20)   NOT NULL,
    CONSTRAINT PK_ETL_Watermark PRIMARY KEY (SourceSystem, EntityName)
);

INSERT INTO dbo.ETL_Watermark (SourceSystem, EntityName, WatermarkValue, LastRunUtc, Status)
VALUES ('DummyJSON', 'Carts', '0', SYSUTCDATETIME(), 'Success');
```

#### Staging (line-grain: one row per cart product)

```sql
CREATE TABLE dbo.stg_CartProducts (
    cart_id         BIGINT         NOT NULL,
    user_id         BIGINT         NULL,
    product_id      BIGINT         NULL,
    product_title   NVARCHAR(256)  NULL,
    quantity        INT            NULL,
    price           DECIMAL(18,4)  NULL,
    line_total      DECIMAL(18,4)  NULL,
    cart_total      DECIMAL(18,4)  NULL,
    ingest_ts       DATETIME2(3)   NOT NULL DEFAULT SYSUTCDATETIME(),
    source_file     NVARCHAR(500)  NULL
);
```

#### Curated + MERGE

```sql
CREATE TABLE dbo.CartProducts (
    cart_id         BIGINT         NOT NULL,
    product_id      BIGINT         NOT NULL,
    user_id         BIGINT         NULL,
    product_title   NVARCHAR(256)  NULL,
    quantity        INT            NULL,
    price           DECIMAL(18,4)  NULL,
    line_total      DECIMAL(18,4)  NULL,
    cart_total      DECIMAL(18,4)  NULL,
    last_updated    DATETIME2(3)   NOT NULL,
    is_active       BIT            NOT NULL DEFAULT 1,
    CONSTRAINT PK_CartProducts PRIMARY KEY (cart_id, product_id)
);
GO

CREATE PROCEDURE dbo.usp_MergeCartProducts
AS
BEGIN
    SET NOCOUNT ON;

    MERGE dbo.CartProducts AS t
    USING (
        SELECT cart_id, product_id, user_id, product_title,
               quantity, price, line_total, cart_total,
               MAX(ingest_ts) AS last_updated
        FROM dbo.stg_CartProducts
        GROUP BY cart_id, product_id, user_id, product_title,
                 quantity, price, line_total, cart_total
    ) AS s
    ON t.cart_id = s.cart_id AND t.product_id = s.product_id
    WHEN MATCHED THEN
        UPDATE SET user_id = s.user_id,
                   product_title = s.product_title,
                   quantity = s.quantity,
                   price = s.price,
                   line_total = s.line_total,
                   cart_total = s.cart_total,
                   last_updated = s.last_updated
    WHEN NOT MATCHED THEN
        INSERT (cart_id, product_id, user_id, product_title,
                quantity, price, line_total, cart_total, last_updated)
        VALUES (s.cart_id, s.product_id, s.user_id, s.product_title,
                s.quantity, s.price, s.line_total, s.cart_total, s.last_updated);
END;
GO

CREATE PROCEDURE dbo.usp_UpdateWatermark
    @SourceSystem   NVARCHAR(100),
    @EntityName     NVARCHAR(100),
    @NewWatermark   NVARCHAR(100),
    @RowsExtracted  BIGINT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.ETL_Watermark
    SET WatermarkValue = @NewWatermark,
        LastRunUtc     = SYSUTCDATETIME(),
        RowsExtracted  = @RowsExtracted,
        Status         = 'Success'
    WHERE SourceSystem = @SourceSystem
      AND EntityName   = @EntityName;
END;
```

#### One reporting view

```sql
CREATE VIEW dbo.vw_CartProductSummary AS
SELECT cart_id,
       user_id,
       COUNT(*) AS product_lines,
       SUM(quantity) AS total_units,
       SUM(line_total) AS revenue
FROM dbo.CartProducts
WHERE is_active = 1
GROUP BY cart_id, user_id;
```

**Exit:** Objects exist; watermark seeded; SQL files committed.

---

### 5.4 M3 — Extract + pagination (0:55–1:20)

**Where:** ADF Studio

#### Datasets

| Dataset | Description |
|---|---|
| `DS_REST_Carts` | RestResource → `/carts` |
| `DS_ADLS_Raw_JSON` | JSON/binary on `api/dummyjson/carts/yyyy/MM/dd/HH/` |

#### DummyJSON pagination (`limit` + `skip`)

Use pipeline variables:

```text
skip     (Int)     = 0
limit    (Int)     = 10
hasMore  (Boolean) = true
pageNum  (Int)     = 1
```

Until condition (stop when page returns fewer than `limit` rows, or after a max page safety count):

```text
@equals(variables('hasMore'), false)
```

Request URL pattern:

```text
@concat('https://dummyjson.com/carts?limit=', string(variables('limit')), '&skip=', string(variables('skip')))
```

After each page:

```text
skip    = @add(variables('skip'), variables('limit'))
pageNum = @add(variables('pageNum'), 1)
hasMore = false when returned carts length < limit (or total reached)
```

Write each page to ADLS with a unique name, e.g.:

```text
@concat('carts_page_', string(variables('pageNum')), '_', formatDateTime(utcnow(), 'yyyyMMddHHmmss'), '.json')
```

- [ ] Manual run lands 2–3 page files under `raw/`
- [ ] If clock ≥ 1:20 and not done → **single-page Copy only**

**Exit:** Raw JSON files visible in ADLS.

---

### 5.5 M4 — Flatten → staging (1:20–1:40)

**Where:** ADF Studio

Data flow: `df_flatten_carts`

1. **Source:** ADLS raw JSON  
2. **Flatten:** unroll `carts` then `products` (or equivalent path for the landed payload)  
3. **Derived Column:** cast types; set `ingest_ts = currentUTC()`  
4. **Sink:** `dbo.stg_CartProducts` (truncate before load)

Example derived mappings (adjust to actual JSON shape after first land):

```text
cart_id       = carts.id
user_id       = carts.userId
product_id    = carts.products.id
product_title = carts.products.title
quantity      = toInteger(carts.products.quantity)
price         = toDecimal(carts.products.price, 18, 4)
line_total    = toDecimal(carts.products.total, 18, 4)
cart_total    = toDecimal(carts.total, 18, 4)
ingest_ts     = currentUTC()
```

**Exit:** Staging row count matches flattened products.

---

### 5.6 M5 — End-to-end orchestration (1:40–1:55)

**Where:** ADF Studio

Pipeline: `pl_ingest_carts`

```text
GetWatermark (Lookup)
    │
    ▼
UntilHasMore (limit/skip pages → ADLS raw)
    │
    ▼
FlattenAndLoad (Execute Data Flow → staging)
    │
    ▼
MergeToCurated (usp_MergeCartProducts)
    │
    ▼
UpdateWatermark (usp_UpdateWatermark)  ← only on success
    │
    ▼ (on failure)
Do NOT update watermark
```

| Step | Activity | Notes |
|---|---|---|
| 1 | Lookup | `SELECT WatermarkValue FROM dbo.ETL_Watermark WHERE SourceSystem='DummyJSON' AND EntityName='Carts'` |
| 2 | Until / Copy | Extract pages to ADLS |
| 3 | Execute Data Flow | Flatten → staging |
| 4 | Stored Procedure | `usp_MergeCartProducts` |
| 5 | Stored Procedure | `usp_UpdateWatermark` — **simulated** watermark (e.g. max `cart_id` or `@utcnow()`), clearly labeled |

Watermark rule (DOCX): **never advance on failure.**

Optional if ≤5 minutes remain:

- Activity retry: 3, interval 30–45s on Copy/Lookup  
- Failure path → insert into `ETL_ErrorLog` (if created)

**Exit:** Curated loaded; watermark advanced only after success.

---

### 5.7 M6 — Prove + Git (1:55–2:00)

**Where:** ADF Studio + VS Code + GitHub

- [ ] Manual pipeline run succeeds  
- [ ] Raw files in ADLS  
- [ ] Staging populated  
- [ ] Curated MERGE correct (or gap documented)  
- [ ] Watermark updated  
- [ ] Reporting view returns rows  
- [ ] SQL scripts committed; ADF Git artifacts on remote  

**Defer:** schedule trigger (if adding later: concurrency = **1**).

---

## 6. DOCX Reference Patterns (Do Not Build in 2 Hours)

Keep these as architecture knowledge from the source DOCX. Implement only when replacing DummyJSON with a real API or extending past the timebox.

### 6.1 API Key linked service (reference)

Store key in Key Vault; reference via `LS_KeyVault`. Not used for DummyJSON.

### 6.2 OAuth2 client credentials (reference)

Web activity → token endpoint → `Authorization: Bearer @{variables('token')}` on Copy. Rotate secrets via Key Vault.

### 6.3 Cursor pagination (reference)

Until loop with `cursor` / `next_cursor` / `has_more`. DummyJSON uses `limit`/`skip` instead.

### 6.4 True incremental watermark (reference)

Call API with `updated_after=@variables('lastWatermark')` and advance with `MAX(updated_at)` from extracted data. DummyJSON does not support this contract — simulate only and label it.

---

## 7. Validation & Definition of Done

### 7.1 2-hour definition of done

- [ ] ADF connected to GitHub  
- [ ] Raw JSON in ADLS under `api/dummyjson/carts/...`  
- [ ] Flattened rows in `dbo.stg_CartProducts`  
- [ ] Curated `dbo.CartProducts` loaded via MERGE (or explicitly noted if skipped)  
- [ ] `ETL_Watermark` updated after successful run only  
- [ ] At least one reporting view works  
- [ ] SQL scripts + ADF JSON present in GitHub  

### 7.2 Quick validation queries

```sql
SELECT * FROM dbo.ETL_Watermark WHERE SourceSystem = 'DummyJSON' AND EntityName = 'Carts';
SELECT COUNT(*) AS staging_rows FROM dbo.stg_CartProducts;
SELECT COUNT(*) AS curated_rows FROM dbo.CartProducts;
SELECT TOP 20 * FROM dbo.vw_CartProductSummary;
```

---

## 8. Best Practices

### 8.1 During the 2-hour run

- One pipeline only: `pl_ingest_carts`
- Small pages (`limit=10`); cap pages for safety
- Prefer Managed Identity for Azure resources
- Keep watermark update as the **last success step**
- Commit early (SQL + docs) even before the pipeline is perfect

### 8.2 After the timebox (optional hardening)

- Activity retries 3–5; interval 30–60s  
- `ETL_ErrorLog` + dead-letter path under `/raw/errors/`  
- Diagnostic settings → Log Analytics  
- Schedule trigger with concurrency = 1  
- Key Vault + OAuth when moving off DummyJSON  
- Bicep + CI/CD only after the pipeline is proven  

### 8.3 Idempotency

- Truncate staging before each load (or equivalent)  
- MERGE so re-runs do not duplicate curated keys  
- Unique ADLS file names per page  

---

## 9. Appendix

### 9.1 Useful ADF expressions

```text
@activity('GetWatermark').output.firstRow.WatermarkValue
@variables('skip')
@concat('https://dummyjson.com/carts?limit=', string(variables('limit')), '&skip=', string(variables('skip')))
@concat('carts_page_', string(variables('pageNum')), '_', formatDateTime(utcnow(), 'yyyyMMddHHmmss'), '.json')
@pipeline().RunId
```

### 9.2 Microsoft docs

| Topic | Link |
|---|---|
| REST connector & pagination | https://learn.microsoft.com/en-us/azure/data-factory/connector-rest |
| Flatten transformation | https://learn.microsoft.com/en-us/azure/data-factory/data-flow-flatten |
| Azure SQL MI auth | https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-aad-overview |
| Pipelines & retries | https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipelines-activities |
| ADLS best practices | https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices |

### 9.3 DummyJSON sample response shape (for flatten planning)

```json
{
  "carts": [
    {
      "id": 1,
      "products": [
        {
          "id": 168,
          "title": "Example Product",
          "price": 9.99,
          "quantity": 2,
          "total": 19.98
        }
      ],
      "total": 19.98,
      "userId": 1
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 10
}
```

---

*End of Execution Runbook — Project 1 Enterprise Integration Pipeline (2-Hour Delivery)*

Source of truth for architecture: `Project1_Enterprise_Integration_Pipeline_Implementation.docx`.  
This runbook is the timeboxed Git-controlled execution guide against DummyJSON `/carts`.

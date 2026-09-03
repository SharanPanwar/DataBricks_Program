# Architecture

## Flow

```text
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   ADLS Gen2     │  │  Google Drive   │  │   Confluence    │
│ orders           │  │ products        │  │ customers       │
│ order_items      │  │                 │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    Unity Catalog · bronze
                              ▼
                    Unity Catalog · silver
                 (clean + joins → order_lines_enriched)
                              ▼
                    Unity Catalog · gold
                         (aggregates / KPIs)
```

## Why each source

| Source | Owns | Rationale |
|---|---|---|
| ADLS Gen2 | Orders and line items | System-generated transactional files landed in the lake |
| Google Drive | Product catalog | Merchandising maintains a shared Sheet / CSV |
| Confluence | Customer registry | Ops publishes the master list as a wiki attachment / table |

## Layers

| Layer | Purpose |
|---|---|
| Bronze | Raw-ish land from each source; add `ingestion_ts`, `source_system` |
| Silver | Types, cleanses, dedupes, enforces FKs, builds enriched fact |
| Gold | Business aggregates for dashboards |

## Catalog (from `notebooks/00_setup_uc_and_paths.ipynb`)

- Catalog: `sample_pipeline`
- Schemas: `bronze`, `silver`, `gold`
- ADLS landing root: `abfss://practice-ecommerce@stpracticeecom.dfs.core.windows.net/landing/sample_pipeline/`
  - `adls/orders/`, `adls/order_items/`
  - `google_drive/products/`
  - `confluence/customers/`
- Edit `STORAGE_ACCOUNT` / `CONTAINER` in the setup Config cell if your lab uses different names.

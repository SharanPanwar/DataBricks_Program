# Cement Plant Reliability Lakehouse POC

## Project Proposal and Architecture

| Field | Value |
|---|---|
| **Project** | Cement Plant Equipment Reliability and Operations Visibility |
| **Team** | SparkSquad |
| **Domain** | Cement manufacturing — equipment health, maintenance, and production impact |
| **Platforms** | Azure Functions, Azure Data Lake Storage Gen2, Azure Databricks, Power BI |
| **Scope** | Single plant, synthetic incremental data, medallion lakehouse, executive dashboard |

---

## 1. Executive summary

This proof of concept establishes an end-to-end lakehouse for cement plant reliability and operations visibility. Synthetic, industry-realistic equipment and maintenance data for one cement plant is generated as Parquet, landed in Azure Data Lake Storage Gen2, refined in Azure Databricks through bronze, silver, and gold layers, and presented in Power BI.

A timer-triggered Azure Function executes a stateful Python simulator. Each execution advances one simulated operating day and writes raw Parquet to the lake. Databricks ingests landing files, applies cleansing and conformance, and publishes KPI models. Power BI consumes curated gold tables.

The architecture is intentionally lean: Azure Functions and object storage form the generation and landing path; Event Hubs and a separate always-on API tier are excluded. The result is a reusable pattern to surface unplanned-downtime risk, prioritize maintenance, and relate asset condition to production impact.

---

## 2. Business problem and value

### 2.1 Problem statement

Cement plants depend on critical assets including kilns, mills, fans, conveyors, packers, and utilities. Condition, status, and maintenance signals are often fragmented, delayed, or inconsistent. Without a unified analytical pipeline, reliability and production teams cannot reliably:

- Detect degrading equipment before failure
- Prioritize work orders by risk and production impact
- Quantify downtime and failure hotspots
- Measure maintenance effectiveness from alert through work-order closure

### 2.2 Solution

The solution delivers a complete lakehouse demonstration that:

1. Simulates plant equipment state over time, including degradation and repair
2. Lands intentionally imperfect raw files consistent with industrial source systems
3. Cleanses and models data in Databricks (bronze, silver, gold)
4. Presents KPIs in Power BI for maintenance, production, and plant leadership

### 2.3 Stakeholders

| Stakeholder | Benefit |
|---|---|
| Maintenance and reliability | Earlier threshold detection and clearer work-order priority |
| Production | Visibility of downtime versus throughput |
| Plant leadership | Consolidated view of health, alerts, and backlog |
| Data and platform teams | Reusable Azure and Databricks reference pattern |

### 2.4 Success criteria

- Day-over-day continuity of asset state for representative equipment
- Intentionally imperfect raw data with cleansing performed in silver
- Complete medallion flow from landing through gold
- Power BI coverage of plant health, alerts, work-order backlog, and failure hotspots
- Deployment within free-tier and low-cost Azure and Databricks constraints

---

## 3. Scope

### 3.1 Included

| Item | Definition |
|---|---|
| Plants | One cement plant |
| Equipment | Standard cement equipment types: kiln, mill, crusher, conveyor, packer, compressor, fan, yard EV |
| History | Approximately one year of simulated operating days, generated incrementally |
| File format | Parquet |
| Landing | ADLS Gen2 under the project landing path |
| Generation compute | Azure Functions (timer-triggered Python) |
| Analytics | Azure Databricks medallion architecture with Unity Catalog |
| Presentation | Power BI on gold KPIs |
| Data quality | Controlled defects in raw and bronze data for silver transformation |

### 3.2 Excluded

| Item | Rationale |
|---|---|
| Multiple plants or companies | Single-site scope maintains clarity of volume and narrative |
| Event Hubs / streaming bus | Not required at POC data volume; no free-tier offering |
| Separate App Service API or API-pull ingest | Databricks reads lake files directly |
| Live OT / SCADA connectors | Synthetic generation substitutes for plant systems |
| Machine learning training and serving | Outside analytical lakehouse demonstration |
| Production SLAs, private networking, enterprise SSO | Beyond POC hardening requirements |

---

## 4. Architecture

### 4.1 Data flow

```text
┌─────────────────────────────────────┐
│  Timer (approximately 8–10 minutes) │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Azure Function (Python)            │
│  • Stateful plant simulator         │
│  • Advances one simulated day       │
│  • Emits messy Parquet batches      │
│  • Updates simulator checkpoint     │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  ADLS Gen2 / Blob landing           │
│  Raw Parquet (source of truth)      │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Databricks                         │
│  Auto Loader / file read            │
│  → Bronze (raw)                     │
│  → Silver (clean / conform)         │
│  → Gold (KPIs)                      │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Power BI                           │
└─────────────────────────────────────┘
```

### 4.2 Design principles

1. **Lake-first storage** — Durable raw data resides in object storage.
2. **File-based ingest** — Databricks reads landing files; Auto Loader does not call external HTTP APIs.
3. **Stateful simulation** — Each run continues from the prior asset state.
4. **Time compression** — Each timer interval corresponds to one simulated plant day (approximately 8–10 minutes wall clock).
5. **Imperfect source data** — Bronze preserves source defects; silver performs cleansing.
6. **Cost discipline** — Prefer Azure Functions and Storage; exclude paid streaming services.

### 4.3 Architecture decisions

| Option | Decision | Rationale |
|---|---|---|
| Event Hubs | Excluded | Unnecessary at POC volume; not free-tier |
| Custom API as Auto Loader source | Excluded | Auto Loader monitors cloud files only |
| App Service always-on API | Excluded | Timer-triggered Function is sufficient |
| Multi-plant generation | Excluded | Single plant keeps volume and story clear |
| Generator writing only to Databricks | Excluded | Landing zone reflects standard lakehouse practice |

---

## 5. Data design

### 5.1 Domain model

Equipment types follow shared industry standards and are instantiated as assets within one plant.

**Dimensions**

| Entity | Purpose |
|---|---|
| `dim_equipment_type` | Kiln, mill, crusher, conveyor, packer, compressor, fan, EV |
| `dim_failure_mode` | Threshold-oriented failure codes per equipment type |
| `dim_part_catalog` | Replaceable parts linked to equipment types |
| `dim_plant` | Plant master |
| `dim_production_line` | Pyro, grinding, packing, and related stages |
| `dim_machine` | Asset instances |

**Facts**

| Entity | Grain | Purpose |
|---|---|---|
| `fact_machine_daily` | One row per machine per `sim_date` | Operating state and metrics |
| `fact_alert_event` | One row per alert | Threshold and condition events |
| `fact_work_order` | One row per work order | Maintenance response |
| `fact_part_replacement` | One row per replacement | Parts consumed on work orders |
| `fact_production_daily` | One row per line per `sim_date` | Throughput and downtime |

Raw schemas (generated and ingested into bronze), including sample values, are defined in the [Data Generation Specification](Data_Generation_Spec.md).

### 5.2 Incremental continuity

Asset state on day *N* is a function of day *N−1* and intervening actions:

- **Yard EV:** Day 1 battery 80% (operating) → Day 2 battery 50% (low charge) → Day 3 battery 90% (operating after charge).
- **Ball mill:** Rising vibration → alert and work order → part replacement → metrics return to normal.

The generator persists a checkpoint so each execution resumes correctly.

### 5.3 Volume assumptions (per generator run)

| Item | Estimate |
|---|---|
| Machines | Approximately 40–60 |
| Daily snapshot rows | Approximately 50, plus limited duplicate noise |
| Alerts, work orders, parts, production | Tens of rows combined |
| Payload size | Approximately 100–250 KB Parquet |
| One-year simulation | Tens of thousands of daily rows |

Timer interval controls the rate of simulated-time advance, not row count per run.

### 5.4 Controlled data defects

Raw and bronze data include controlled defects:

| Defect | Silver treatment |
|---|---|
| Null or missing metrics | Impute, drop, or quarantine |
| Numerics stored as text (`79C`, `50%`, `6,8`) | Parse and cast |
| Status synonyms (`RUN`, `running`, `Operating`) | Map to canonical enumeration |
| Duplicate natural keys | Deduplicate |
| Mixed or invalid dates | Standardize to date |
| Orphan machine identifiers | Quarantine |
| Impossible values | Range validation |
| Occasional schema drift | Explicit column handling |

A documented mess profile preserves reproducibility while maintaining continuity on representative assets (mill, kiln, EV).

### 5.5 Continuity examples

| `sim_date` | Machine | Key metric | Status | Narrative |
|---|---|---|---|---|
| 2025-01-10 | `M-ACM-EV-03` | battery 80% | operating | Normal shift |
| 2025-01-11 | `M-ACM-EV-03` | battery 50% | low_charge | Not charged overnight |
| 2025-01-12 | `M-ACM-EV-03` | battery 90% | operating | Charged after prior day |
| 2025-01-10 | `M-ACM-MILL-01` | vib 3.2 mm/s | operating | Healthy |
| 2025-01-11 | `M-ACM-MILL-01` | vib 6.8 mm/s | warning | Alert raised |
| 2025-01-12 | `M-ACM-MILL-01` | vib 3.5 mm/s | operating | Bearing work completed |

---

## 6. Storage layout

| Property | Value |
|---|---|
| Account | Azure Storage with hierarchical namespace (ADLS Gen2) |
| Format | Parquet |

```text
abfss://<container>@<storage-account>.dfs.core.windows.net/
└── landing/
    └── cement/
        ├── dim/
        │   ├── equipment_type/
        │   ├── failure_mode/
        │   ├── part_catalog/
        │   ├── plant/
        │   ├── production_line/
        │   └── machine/
        ├── fact/
        │   ├── machine_daily/sim_date=YYYY-MM-DD/batch_id=.../
        │   ├── alert_event/sim_date=.../batch_id=.../
        │   ├── work_order/...
        │   ├── part_replacement/...
        │   └── production_daily/...
        └── _simulator/
            └── state/
```

Fact files include provenance columns: `batch_id`, `generated_at`, `sim_day_index`, `source_system`.

---

## 7. Databricks medallion layers

| Layer | Schema | Contents |
|---|---|---|
| Bronze | `cement_poc.bronze` | Raw tables from Auto Loader, including `_bronze_ingestion_ts` and `_source_file` |
| Silver | `cement_poc.silver` | Typed, deduplicated, FK-validated entities; quarantine for rejects |
| Gold | `cement_poc.gold` | Business aggregates for Power BI |

### 7.1 Gold KPIs

- **Plant daily:** assets in warning or critical status, open work orders, downtime hours, cement and clinker tonnage, critical alerts
- **Asset reliability:** uptime percentage, alert count, mean time to repair, parts replaced
- **Failure hotspots:** alerts by equipment type and failure mode

### 7.2 Ingestion

Databricks Auto Loader (or equivalent incremental file read) consumes the landing path. Bronze remains faithful to source files; transformations occur in silver.

---

## 8. Component responsibilities

| Component | Responsibility |
|---|---|
| Azure Function (timer) | Execute simulator; write Parquet; update checkpoint |
| ADLS Gen2 landing | Durable raw store |
| Databricks | Ingest, cleanse, model, and publish gold |
| Power BI | Visualize gold KPIs |

---

## 9. Cost posture

| Choice | Rationale |
|---|---|
| Azure Functions | Fits sparse timer executions within free monthly allotments |
| Blob / ADLS landing | Small Parquet footprint fits free storage quotas |
| No Event Hubs | Avoids paid streaming SKUs |
| No App Service API tier | Avoids always-on compute cost |
| One plant, daily grain | Limits storage and Databricks compute |
| Databricks Free Edition, trial, or lab workspace | Sufficient for transform workloads |

Operate the timer during active demonstration windows when compute quotas are constrained. Prefer fewer, larger Parquet files per run.

---


## 12. Open items

| Topic | Status |
|---|---|
| Timer interval (7, 8, or 10 minutes) | To be confirmed |
| Exact machine count within 40–60 | To be confirmed at simulator build |
| Storage account and container names | To be confirmed per subscription |
| Databricks workspace edition | To be confirmed per team access |
| Power BI Import versus DirectQuery | To be confirmed at dashboard build |

---

## 13. Summary

The POC delivers cement equipment reliability and operations visibility on a lean Azure and Databricks lakehouse:

**Azure Function simulator → Parquet on ADLS Gen2 → Databricks bronze / silver / gold → Power BI.**

The design uses one plant, shared equipment types, incremental stateful data, intentionally imperfect raw files, and business KPIs suitable for industrial demonstration.

---

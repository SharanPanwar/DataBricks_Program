# Data Generation Specification

## Raw schema (generated → bronze)

This document defines the **raw Parquet schemas** produced by the data generator and ingested unchanged into **Databricks bronze**.

| Scope | Included |
|---|---|
| Generated raw tables | Yes — eleven tables below |
| Bronze ingest | Yes — same columns as landed Parquet |
| Silver / gold schemas | Not in this document |

**Format:** Parquet  
**Domain path:** `industry/cement/`  
**Provenance on every fact row:** `batch_id`, `generated_at`, `sim_day_index`, `source_system`

Raw files may contain intentional defects (nulls, text numerics, status synonyms, duplicates). Bronze stores these values as landed.

---

## 1. Raw table inventory

| # | Raw table | Kind | Landing folder | Approx. rows | Cadence |
|---|---|---|---|---|---|
| 1 | `dim_asset_type` | Dimension | `dim/asset_type/` | 8 | Bootstrap / refresh |
| 2 | `dim_failure_mode` | Dimension | `dim/failure_mode/` | 12–20 | Bootstrap / refresh |
| 3 | `dim_part_catalog` | Dimension | `dim/part_catalog/` | 15–25 | Bootstrap / refresh |
| 4 | `dim_site` | Dimension | `dim/site/` | 1 | Bootstrap |
| 5 | `dim_line` | Dimension | `dim/line/` | 4–6 | Bootstrap |
| 6 | `dim_asset` | Dimension | `dim/asset/` | ~50 | Bootstrap |
| 7 | `fact_asset_daily` | Fact | `fact/asset_daily/sim_date=.../batch_id=.../` | ~50 per sim day | Each run |
| 8 | `fact_alert_event` | Fact | `fact/alert_event/sim_date=.../batch_id=.../` | ~5–20 per sim day | Each run |
| 9 | `fact_work_order` | Fact | `fact/work_order/sim_date=.../batch_id=.../` | ~2–8 per sim day | Each run |
| 10 | `fact_part_replacement` | Fact | `fact/part_replacement/sim_date=.../batch_id=.../` | ~0–4 per sim day | Each run |
| 11 | `fact_production_daily` | Fact | `fact/production_daily/sim_date=.../batch_id=.../` | ~5–6 per sim day | Each run |

**Bronze tables (illustrative names):** `cement_poc.bronze.dim_asset_type`, `...fact_asset_daily`, and matching names for each raw table above. Auto Loader may add ingest metadata columns (for example `_bronze_ingestion_ts`, `_source_file`); those are platform-added and are not part of the generator schema.

### Cement meaning of generic names

| Raw table | Cement meaning |
|---|---|
| `dim_site` | Cement plant |
| `dim_line` | Production line |
| `dim_asset` | Machine / equipment instance |
| `dim_asset_type` | Kiln, mill, crusher, conveyor, packer, and related |
| `fact_asset_daily` | Daily machine operating snapshot |
| `fact_production_daily` | Clinker / cement tonnage, energy, downtime |

### Landing root

```text
{LANDING_ROOT}/industry/cement/
├── dim/...
└── fact/...
```

---

## 2. Raw dimension schemas

### 2.1 `dim_asset_type`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `asset_type_id` | string | No | Primary key | `AT-KILN-01`, `AT-MILL-01`, `AT-CRUSH-01`, `AT-CONV-01`, `AT-PACK-01`, `AT-COMP-01`, `AT-FAN-01`, `AT-EV-01` |
| `name` | string | No | Display name | `Rotary Kiln`, `Ball Mill`, `Jaw Crusher`, `Belt Conveyor`, `Bagging Packer`, `Air Compressor`, `ID Fan`, `Yard EV Loader` |
| `category` | string | No | Process category | `pyroprocessing`, `grinding`, `crushing`, `material_handling`, `packing`, `utilities`, `mobile` |
| `criticality` | string | No | Business criticality | `critical`, `high`, `medium`, `low` |
| `typical_sensors` | string | Yes | Comma-separated sensor list | `shell_temp,vibration,draft`, `vibration,bearing_temp,power_kw`, `battery_pct,motor_temp` |

**Sample rows (raw)**

| asset_type_id | name | category | criticality | typical_sensors |
|---|---|---|---|---|
| `AT-KILN-01` | Rotary Kiln | pyroprocessing | critical | shell_temp,vibration,draft,torque |
| `AT-MILL-01` | Ball Mill | grinding | high | vibration,bearing_temp,power_kw |
| `AT-CONV-01` | Belt Conveyor | material_handling | medium | motor_temp,speed_mps,load_pct |
| `AT-EV-01` | Yard EV Loader | mobile | low | battery_pct,motor_temp,hours |

---

### 2.2 `dim_failure_mode`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `failure_mode_id` | string | No | Primary key | `FM-001`, `FM-002`, `FM-003` |
| `asset_type_id` | string | No | FK → `dim_asset_type` | `AT-KILN-01`, `AT-MILL-01`, `AT-EV-01` |
| `code` | string | No | Stable failure code | `KILN_OVERTEMP`, `HIGH_VIBRATION`, `LOW_BATTERY`, `BELT_SLIP`, `SEAL_FAULT` |
| `description` | string | No | Description | `Kiln shell over-temperature`, `Mill bearing vibration high` |
| `severity` | string | No | Severity label | `critical`, `high`, `medium`, `low` |
| `metric_name` | string | No | Metric that trips this mode | `temp_c`, `vibration_mms`, `battery_pct` |
| `warn_threshold` | double or string | Yes | Warning threshold (may be string if messy) | `350`, `4.5`, `30` |
| `critical_threshold` | double or string | Yes | Critical threshold | `420`, `7.0`, `15` |
| `threshold_unit` | string | Yes | Unit | `C`, `mm/s`, `%` |

**Sample rows (raw)**

| failure_mode_id | asset_type_id | code | description | severity | metric_name | warn_threshold | critical_threshold | threshold_unit |
|---|---|---|---|---|---|---|---|---|
| `FM-001` | `AT-KILN-01` | `KILN_OVERTEMP` | Kiln shell over-temperature | critical | temp_c | 350 | 420 | C |
| `FM-002` | `AT-MILL-01` | `HIGH_VIBRATION` | Mill bearing vibration high | high | vibration_mms | 4.5 | 7.0 | mm/s |
| `FM-003` | `AT-EV-01` | `LOW_BATTERY` | EV battery below threshold | medium | battery_pct | 30 | 15 | % |
| `FM-004` | `AT-CONV-01` | `BELT_SLIP` | Conveyor belt slip | medium | load_pct | 85 | 95 | % |
| `FM-005` | `AT-PACK-01` | `SEAL_FAULT` | Bag seal temperature fault | low | temp_c | 180 | 210 | C |

---

### 2.3 `dim_part_catalog`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `part_id` | string | No | Primary key | `P-BRG-440`, `P-BELT-12`, `P-BAT-EV`, `P-SEAL-9` |
| `asset_type_id` | string | No | FK → `dim_asset_type` | `AT-MILL-01`, `AT-CONV-01`, `AT-EV-01` |
| `part_name` | string | No | Part name | `Trunnion bearing`, `Conveyor belt section`, `Battery pack module`, `Heat seal bar` |
| `mtbf_hours_hint` | int or string | Yes | MTBF hint hours | `8000`, `5000`, `12000`, `3000` |

**Sample rows (raw)**

| part_id | asset_type_id | part_name | mtbf_hours_hint |
|---|---|---|---|
| `P-BRG-440` | `AT-MILL-01` | Trunnion bearing | 8000 |
| `P-BELT-12` | `AT-CONV-01` | Conveyor belt section | 5000 |
| `P-BAT-EV` | `AT-EV-01` | Battery pack module | 12000 |
| `P-SEAL-9` | `AT-PACK-01` | Heat seal bar | 3000 |
| `P-FAN-BRG-2` | `AT-FAN-01` | Fan bearing set | 6000 |

---

### 2.4 `dim_site`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `site_id` | string | No | Primary key (one site) | `SITE-ACM-01` |
| `site_name` | string | No | Site name | `Acme Raigad Cement Works` |
| `capacity_tpd` | int or string | Yes | Design capacity tonnes/day | `5000` |
| `region` | string | Yes | Region | `IN-West` |
| `timezone` | string | Yes | IANA timezone | `Asia/Kolkata` |
| `industry_code` | string | No | Industry pack code | `cement` |

**Sample row (raw)**

| site_id | site_name | capacity_tpd | region | timezone | industry_code |
|---|---|---|---|---|---|
| `SITE-ACM-01` | Acme Raigad Cement Works | 5000 | IN-West | Asia/Kolkata | cement |

---

### 2.5 `dim_line`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `line_id` | string | No | Primary key | `LN-PYRO-01`, `LN-GRND-A`, `LN-PACK-01` |
| `site_id` | string | No | FK → `dim_site` | `SITE-ACM-01` |
| `line_name` | string | No | Line name | `Pyro Line 1`, `Grinding Line A`, `Packing Hall 1` |
| `process_stage` | string | No | Process stage | `pyroprocessing`, `grinding`, `packing` |

**Sample rows (raw)**

| line_id | site_id | line_name | process_stage |
|---|---|---|---|
| `LN-PYRO-01` | `SITE-ACM-01` | Pyro Line 1 | pyroprocessing |
| `LN-GRND-A` | `SITE-ACM-01` | Grinding Line A | grinding |
| `LN-GRND-B` | `SITE-ACM-01` | Grinding Line B | grinding |
| `LN-PACK-01` | `SITE-ACM-01` | Packing Hall 1 | packing |
| `LN-UTIL-01` | `SITE-ACM-01` | Utilities | utilities |

---

### 2.6 `dim_asset`

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `asset_id` | string | No | Primary key | `A-ACM-KILN-01`, `A-ACM-MILL-01`, `A-ACM-EV-03` |
| `site_id` | string | No | FK → `dim_site` | `SITE-ACM-01` |
| `line_id` | string | Yes | FK → `dim_line`; null for mobile | `LN-PYRO-01`, `LN-GRND-A`, `` (empty/null) |
| `asset_type_id` | string | No | FK → `dim_asset_type` | `AT-KILN-01`, `AT-MILL-01`, `AT-EV-01` |
| `asset_tag` | string | Yes | Plant tag | `KILN-RGD-1`, `MILL-A1`, `EV-YARD-03` |
| `install_year` | int or string | Yes | Install year | `2018`, `2019`, `2023` |
| `rated_power_kw` | double or string | Yes | Rated power kW | `4500`, `3200`, `90` |

**Sample rows (raw)**

| asset_id | site_id | line_id | asset_type_id | asset_tag | install_year | rated_power_kw |
|---|---|---|---|---|---|---|
| `A-ACM-KILN-01` | `SITE-ACM-01` | `LN-PYRO-01` | `AT-KILN-01` | KILN-RGD-1 | 2018 | 4500 |
| `A-ACM-MILL-01` | `SITE-ACM-01` | `LN-GRND-A` | `AT-MILL-01` | MILL-A1 | 2019 | 3200 |
| `A-ACM-CONV-07` | `SITE-ACM-01` | `LN-GRND-A` | `AT-CONV-01` | CV-07 | 2020 | 75 |
| `A-ACM-PACK-02` | `SITE-ACM-01` | `LN-PACK-01` | `AT-PACK-01` | PACK-02 | 2021 | 45 |
| `A-ACM-EV-03` | `SITE-ACM-01` | null | `AT-EV-01` | EV-YARD-03 | 2023 | 90 |
| `A-ACM-FAN-01` | `SITE-ACM-01` | `LN-PYRO-01` | `AT-FAN-01` | IDFAN-1 | 2018 | 1200 |

---

## 3. Raw fact schemas

Fact columns may appear as strings in Parquet when the mess profile applies (for example `"6,8"`, `"79C"`, `"50%"`). Bronze retains the landed type/value.

Shared provenance columns on all facts:

| Column | Raw type | Sample values |
|---|---|---|
| `batch_id` | string | `20260320T081000Z` |
| `generated_at` | string (ISO-8601) or timestamp | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | `42` |
| `source_system` | string | `industry_sim_v1` |

---

### 3.1 `fact_asset_daily` (16 columns)

One row per asset per `sim_date` (plus occasional duplicate rows from mess).

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `sim_date` | string | Yes* | Simulated business date (*null/bad format possible in mess) | `2025-01-11`, `11/01/2025` |
| `asset_id` | string | No | Asset id (orphan ids possible in mess) | `A-ACM-MILL-01`, `A-ACM-EV-03`, `A-UNK-999` |
| `site_id` | string | Yes | Site id | `SITE-ACM-01` |
| `asset_type_id` | string | Yes | Asset type | `AT-MILL-01`, `AT-EV-01`, `AT-KILN-01` |
| `status` | string | Yes | Operating status (synonyms in raw) | `operating`, `warning`, `WARNING`, `low_charge`, `Low Charge`, `critical`, `RUN`, `running` |
| `operating_hours` | double or string | Yes | Hours run | `22.0`, `6.5`, `18.5` |
| `power_kw_avg` | double or string | Yes | Average power kW | `2950`, `22.1`, `4100` |
| `vibration_mms` | double or string | Yes | Vibration mm/s | `3.2`, `6.8`, `6,8`, `3.1 mm/s`, null |
| `temp_c` | double or string | Yes | Temp °C (bearing/shell/motor) | `68`, `79C`, `435`, `43.2` |
| `battery_pct` | double or string | Yes | Battery % (EV); else null | `80`, `50%`, `90`, `N/A`, null |
| `throughput_tph` | double or string | Yes | Throughput t/h | `145`, `132`, null |
| `quality_flag` | string | Yes | Quality flag | `ok`, `suspect` |
| `batch_id` | string | No | Batch id | `20260320T081000Z` |
| `generated_at` | string / timestamp | No | Generation timestamp UTC | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | No | Day index | `42` |
| `source_system` | string | No | Source label | `industry_sim_v1` |

**Sample rows — clean continuity (as generated before/aside from mess)**

| sim_date | asset_id | status | vibration_mms | temp_c | battery_pct | operating_hours | power_kw_avg | throughput_tph | quality_flag |
|---|---|---|---|---|---|---|---|---|---|
| 2025-01-10 | A-ACM-EV-03 | operating | null | 41.0 | 80 | 6.5 | 22.1 | null | ok |
| 2025-01-11 | A-ACM-EV-03 | low_charge | null | 43.2 | 50 | 7.0 | 20.4 | null | ok |
| 2025-01-12 | A-ACM-EV-03 | operating | null | 40.5 | 90 | 6.2 | 21.0 | null | ok |
| 2025-01-10 | A-ACM-MILL-01 | operating | 3.2 | 68.0 | null | 22.0 | 2950 | 145 | ok |
| 2025-01-11 | A-ACM-MILL-01 | warning | 6.8 | 79.0 | null | 18.5 | 3010 | 132 | ok |
| 2025-01-12 | A-ACM-MILL-01 | operating | 3.5 | 70.0 | null | 21.0 | 2975 | 148 | ok |
| 2025-01-11 | A-ACM-KILN-01 | critical | 2.1 | 435.0 | null | 24.0 | 4100 | 210 | suspect |

**Sample rows — messy raw (as landed / bronze)**

| sim_date | asset_id | status | vibration_mms | temp_c | battery_pct | notes |
|---|---|---|---|---|---|---|
| 2025-01-11 | A-ACM-MILL-01 | WARNING | `6,8` | `79C` | | text metrics + status synonym |
| 2025-01-11 | a-acm-mill-01 | warning | 6.8 | 79 | | case drift / near-duplicate |
| 2025-01-11 | A-ACM-EV-03 | Low Charge | | 43.2 | `50%` | status + unit in string |
| 2025-01-11 | A-ACM-EV-03 | low_charge | null | 43.2 | 50 | exact duplicate key |
| 2025-01-11 | A-UNK-999 | running | 1.2 | 55 | | orphan asset_id |
| null | A-ACM-CONV-07 | RUN | `-1` | 9999 | | bad date + impossible values |
| 11/01/2025 | A-ACM-MILL-02 | Operating | `3.1 mm/s` | 70 | | alternate date format |

---

### 3.2 `fact_alert_event` (14 columns)

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `event_id` | string | No | Event primary key | `EVT-10041`, `EVT-10042`, `EVT-10055` |
| `event_ts` | string / timestamp | Yes | Event time | `2025-01-11T06:14:22Z` |
| `sim_date` | string | Yes | Simulated date | `2025-01-11` |
| `asset_id` | string | No | Asset id | `A-ACM-MILL-01`, `A-ACM-EV-03`, `A-ACM-KILN-01` |
| `failure_mode_id` | string | Yes | FK → failure mode | `FM-002`, `FM-003`, `FM-001` |
| `metric_name` | string | Yes | Metric name | `vibration_mms`, `battery_pct`, `temp_c` |
| `metric_value` | double or string | Yes | Observed value | `6.8`, `50`, `435`, `6,8` |
| `threshold_value` | double or string | Yes | Threshold breached | `4.5`, `30`, `420` |
| `severity` | string | Yes | Severity | `high`, `medium`, `critical`, `HIGH` |
| `acknowledged` | boolean or string | Yes | Ack flag | `true`, `false`, `True`, `yes`, `0` |
| `batch_id` | string | No | Batch id | `20260320T081000Z` |
| `generated_at` | string / timestamp | No | Generation time | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | No | Day index | `42` |
| `source_system` | string | No | Source | `industry_sim_v1` |

**Sample rows (raw)**

| event_id | event_ts | sim_date | asset_id | failure_mode_id | metric_name | metric_value | threshold_value | severity | acknowledged |
|---|---|---|---|---|---|---|---|---|---|
| EVT-10041 | 2025-01-11T06:14:22Z | 2025-01-11 | A-ACM-MILL-01 | FM-002 | vibration_mms | 6.8 | 4.5 | high | false |
| EVT-10042 | 2025-01-11T18:02:01Z | 2025-01-11 | A-ACM-EV-03 | FM-003 | battery_pct | 50 | 30 | medium | true |
| EVT-10055 | 2025-01-11T11:40:00Z | 2025-01-11 | A-ACM-KILN-01 | FM-001 | temp_c | 435 | 420 | critical | false |
| EVT-10056 | 2025-01-11T11:40:00Z | 2025-01-11 | A-ACM-KILN-01 | FM-001 | temp_c | `435C` | 420 | CRITICAL | no |

---

### 3.3 `fact_work_order` (13 columns)

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `work_order_id` | string | No | Work order id | `WO-7781`, `WO-7782`, `WO-7783` |
| `opened_sim_date` | string | Yes | Open date | `2025-01-11` |
| `closed_sim_date` | string | Yes | Close date; empty if open | `2025-01-11`, null, `` |
| `asset_id` | string | No | Asset id | `A-ACM-MILL-01`, `A-ACM-KILN-01` |
| `alert_event_id` | string | Yes | Related alert | `EVT-10041`, `EVT-10055`, null |
| `wo_type` | string | Yes | Work order type | `corrective`, `service`, `preventive`, `Corrective` |
| `technician` | string | Yes | Technician name | `R. Sharma`, `Yard Ops`, null |
| `downtime_hours` | double or string | Yes | Downtime hours | `3.5`, `0.5`, null |
| `status` | string | Yes | Status | `open`, `closed`, `OPEN`, `Closed` |
| `batch_id` | string | No | Batch id | `20260320T081000Z` |
| `generated_at` | string / timestamp | No | Generation time | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | No | Day index | `42` |
| `source_system` | string | No | Source | `industry_sim_v1` |

**Sample rows (raw)**

| work_order_id | opened_sim_date | closed_sim_date | asset_id | alert_event_id | wo_type | technician | downtime_hours | status |
|---|---|---|---|---|---|---|---|---|
| WO-7781 | 2025-01-11 | 2025-01-11 | A-ACM-MILL-01 | EVT-10041 | corrective | R. Sharma | 3.5 | closed |
| WO-7782 | 2025-01-11 | null | A-ACM-KILN-01 | EVT-10055 | corrective | null | null | open |
| WO-7783 | 2025-01-11 | 2025-01-11 | A-ACM-EV-03 | EVT-10042 | service | Yard Ops | 0.5 | closed |

---

### 3.4 `fact_part_replacement` (11 columns)

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `replacement_id` | string | No | Replacement id | `PR-2201` |
| `sim_date` | string | Yes | Replacement date | `2025-01-11` |
| `asset_id` | string | No | Asset id | `A-ACM-MILL-01` |
| `part_id` | string | No | Part id | `P-BRG-440` |
| `work_order_id` | string | Yes | Related WO | `WO-7781` |
| `qty` | int or string | Yes | Quantity | `1`, `2` |
| `reason` | string | Yes | Reason | `high_vibration`, `scheduled`, `seal_fault` |
| `batch_id` | string | No | Batch id | `20260320T081000Z` |
| `generated_at` | string / timestamp | No | Generation time | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | No | Day index | `42` |
| `source_system` | string | No | Source | `industry_sim_v1` |

**Sample rows (raw)**

| replacement_id | sim_date | asset_id | part_id | work_order_id | qty | reason |
|---|---|---|---|---|---|---|
| PR-2201 | 2025-01-11 | A-ACM-MILL-01 | P-BRG-440 | WO-7781 | 1 | high_vibration |
| PR-2202 | 2025-01-11 | A-ACM-PACK-02 | P-SEAL-9 | WO-7790 | 1 | seal_fault |

---

### 3.5 `fact_production_daily` (11 columns)

| Column | Raw type | Nullable | Description | Sample values |
|---|---|---|---|---|
| `sim_date` | string | Yes | Simulated date | `2025-01-11` |
| `site_id` | string | No | Site id | `SITE-ACM-01` |
| `line_id` | string | No | Line id | `LN-PYRO-01`, `LN-GRND-A`, `LN-PACK-01` |
| `output_primary_t` | double or string | Yes | Primary output tonnes (cement: clinker) | `4800`, null |
| `output_secondary_t` | double or string | Yes | Secondary output tonnes (cement: cement) | `3100`, `3050`, null |
| `energy_mwh` | double or string | Yes | Energy MWh | `920`, `410`, `55` |
| `downtime_hours` | double or string | Yes | Downtime hours | `2.0`, `3.5`, `0.5` |
| `batch_id` | string | No | Batch id | `20260320T081000Z` |
| `generated_at` | string / timestamp | No | Generation time | `2026-03-20T08:10:00Z` |
| `sim_day_index` | int or string | No | Day index | `42` |
| `source_system` | string | No | Source | `industry_sim_v1` |

**Sample rows (raw)**

| sim_date | site_id | line_id | output_primary_t | output_secondary_t | energy_mwh | downtime_hours |
|---|---|---|---|---|---|---|
| 2025-01-11 | SITE-ACM-01 | LN-PYRO-01 | 4800 | null | 920 | 2.0 |
| 2025-01-11 | SITE-ACM-01 | LN-GRND-A | null | 3100 | 410 | 3.5 |
| 2025-01-11 | SITE-ACM-01 | LN-GRND-B | null | 2800 | 390 | 1.0 |
| 2025-01-11 | SITE-ACM-01 | LN-PACK-01 | null | 3050 | 55 | 0.5 |

---

## 4. Volumes (raw batches)

| Batch type | Contents | Approximate size |
|---|---|---|
| One incremental run (1 sim day) | ~70–100 fact rows across five fact tables | 100–250 KB |
| Bootstrap dimensions | ~80–110 dim rows | &lt; 1 MB |
| Bootstrap + 30 sim days | ~1,500 daily rows + events | 1–3 MB |
| Bootstrap + 90 sim days | ~4,500 daily rows + events | 3–5 MB |
| ~1 year daily grain | ~18,000 `fact_asset_daily` rows + events | Still small for bronze |

---

## 5. Mess profile applied to raw / bronze

| Defect | Target rate | Example in raw column |
|---|---|---|
| Null metric | ~8% | `vibration_mms` = null |
| Duplicate natural key | ~2% | Two rows same `asset_id` + `sim_date` |
| Status synonym | ~5% of status fields | `RUN`, `WARNING`, `Low Charge` |
| Numeric as text | ~5% | `79C`, `50%`, `6,8` |
| Bad / alternate date | ~1–2% | `11/01/2025`, null `sim_date` |
| Orphan `asset_id` | ~1% | `A-UNK-999` |
| Out-of-range value | ~1–2% | `temp_c` = 9999, `vibration_mms` = -1 |
| Extra column drift | Rare | Occasional `operator_name` in a file |

---

## 6. End-to-end raw path

```text
Generator
  → Parquet under industry/cement/dim|fact/...
  → Databricks Auto Loader
  → Bronze tables (same business columns + optional ingest metadata)
```

---


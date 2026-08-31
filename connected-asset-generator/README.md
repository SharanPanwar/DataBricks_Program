# Connected Asset Generator

Synthetic operational data source for the Azure Databricks POC. Generates multi-domain
connected-asset data (telemetry, events, maintenance) into **Azure SQL Database**.

## Architecture

```
00:00  Azure Function (Timer)  →  writes to Azure SQL
01:00  ADF                      →  reads via HTTP API functions (later)
```

The generator is a Python package — not a monolithic script. It maintains per-asset state
and produces causal, domain-aware data with controlled quality issues.

## Project structure

```
connected-asset-generator/
  schema/           # Azure SQL DDL (T-SQL)
  config/           # generation.yaml + domain YAMLs (Step 2)
  src/asset_generator/
    models.py       # Pydantic entity models
    config.py       # YAML loader
    storage/        # Azure SQL connection + bulk insert
    cli.py          # CLI entrypoint
  tests/
```

## Setup

```bash
cd connected-asset-generator
pip install -e ".[dev]"
```

Set your Azure SQL connection string:

```bash
# PowerShell
$env:AZURE_SQL_CONNECTION_STRING = "mssql+pyodbc://user:pass@server.database.windows.net/db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes"
```

Requires **ODBC Driver 18 for SQL Server** installed locally.

## Commands (roadmap)

| Command | Status | Description |
|---------|--------|-------------|
| `asset-generator init` | Step 4 | Apply schema + seed master data |
| `asset-generator generate-history` | Step 9 | Backfill 1 month of history |
| `asset-generator generate-daily` | Step 9 | Generate one day's data |

## Schema overview

**Master data:** `domains`, `locations`, `asset_types`, `assets`, `operators`, `asset_state`

**Transactional:** `telemetry` + 8 domain tables, `events`, `maintenance`

**Metadata:** `generation_batches`, `asset_state_history`

## Domains

AUTOMOTIVE, CONSTRUCTION, MEDICAL, AEROSPACE, INDUSTRIAL, ENERGY, AGRICULTURE, ELECTRONICS

## Medium profile (default)

| Parameter | Value |
|-----------|-------|
| Assets | 2,000 (~250/domain) |
| Locations | 50 |
| Operators | 500 |
| History | 30 days |
| Telemetry interval | 5 minutes |
| Active assets/day | ~750 |
| Telemetry/day | ~100k–150k |

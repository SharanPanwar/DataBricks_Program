# SparkSquad-POC

Industrial equipment reliability and operations visibility proof of concept.

| Item | Definition |
|---|---|
| **Domain pack** | Cement manufacturing (one plant) |
| **Framework** | Industry-agnostic simulator engine with swappable domain packs |
| **Platform stack** | Azure Functions → ADLS Gen2 (Parquet) → Databricks (bronze / silver / gold) → Power BI |

## Documents

| Document | Description |
|---|---|
| [Project Proposal and Architecture](docs/Cement_Plant_Reliability_POC_Proposal.md) | Problem statement, scope, architecture, roadmap |
| [Data Generation Specification](docs/Data_Generation_Spec.md) | Raw schemas generated and ingested into bronze (columns + samples) |

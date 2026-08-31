"""Connected Asset synthetic operational data source."""

__version__ = "0.1.0"

DOMAINS = (
    "AUTOMOTIVE",
    "CONSTRUCTION",
    "MEDICAL",
    "AEROSPACE",
    "INDUSTRIAL",
    "ENERGY",
    "AGRICULTURE",
    "ELECTRONICS",
)

ASSET_STATES = (
    "ACTIVE",
    "DEGRADED",
    "WARNING",
    "FAILED",
    "UNDER_MAINTENANCE",
)

SEVERITY_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

MAINTENANCE_STATUSES = ("SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED")

# Maps domain_id to the domain-specific telemetry table name suffix.
DOMAIN_TELEMETRY_TABLES: dict[str, str] = {
    "AUTOMOTIVE": "telemetry_automotive",
    "CONSTRUCTION": "telemetry_construction",
    "MEDICAL": "telemetry_medical",
    "AEROSPACE": "telemetry_aerospace",
    "INDUSTRIAL": "telemetry_industrial",
    "ENERGY": "telemetry_energy",
    "AGRICULTURE": "telemetry_agriculture",
    "ELECTRONICS": "telemetry_electronics",
}

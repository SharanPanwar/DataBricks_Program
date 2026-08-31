"""Pydantic models for source-system entities."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from asset_generator import ASSET_STATES, DOMAINS, SEVERITY_LEVELS


class Domain(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain_id: str
    name: str
    description: str | None = None


class Location(BaseModel):
    location_id: str
    location_name: str
    location_type: str
    city: str
    state: str | None = None
    country: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    manager: str | None = None
    status: str = "ACTIVE"


class AssetType(BaseModel):
    asset_type_id: str
    domain_id: str
    name: str
    description: str | None = None


class Operator(BaseModel):
    operator_id: str
    name: str
    role: str
    department: str
    hire_date: date
    certification_level: str | None = None
    status: str = "ACTIVE"


class Asset(BaseModel):
    asset_id: str
    domain_id: str
    asset_type_id: str
    manufacturer: str
    model: str
    serial_number: str
    location_id: str
    operator_id: str | None = None
    installation_date: date
    purchase_cost: Decimal | None = None
    status: str = "ACTIVE"
    expected_lifespan_years: int | None = None


class AssetState(BaseModel):
    asset_id: str
    state: Literal["ACTIVE", "DEGRADED", "WARNING", "FAILED", "UNDER_MAINTENANCE"] = "ACTIVE"
    battery_level: Decimal | None = None
    fuel_level: Decimal | None = None
    operating_hours: Decimal = Field(default=Decimal("0"))
    odometer: Decimal | None = None
    health_score: int = Field(default=100, ge=0, le=100)
    last_maintenance: datetime | None = None


class TelemetryRow(BaseModel):
    telemetry_id: str
    asset_id: str
    recorded_at: datetime
    temperature: Decimal | None = None
    pressure: Decimal | None = None
    vibration: Decimal | None = None
    power_consumption: Decimal | None = None
    voltage: Decimal | None = None
    current_amps: Decimal | None = None
    sensor_status: str | None = "NORMAL"
    batch_id: str | None = None


class EventRow(BaseModel):
    event_id: str
    asset_id: str
    occurred_at: datetime
    event_type: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    error_code: str | None = None
    description: str | None = None
    resolved: bool = False
    resolution_timestamp: datetime | None = None
    batch_id: str | None = None


class MaintenanceRow(BaseModel):
    maintenance_id: str
    asset_id: str
    maintenance_date: datetime
    maintenance_type: str
    reason: str
    technician_id: str | None = None
    parts_replaced: str | None = None
    labor_hours: Decimal | None = None
    parts_cost: Decimal | None = None
    labor_cost: Decimal | None = None
    total_cost: Decimal | None = None
    status: str = "COMPLETED"
    batch_id: str | None = None


class GenerationBatch(BaseModel):
    batch_id: str
    batch_date: date
    profile: str
    status: str = "COMPLETED"
    telemetry_rows: int = 0
    event_rows: int = 0
    maintenance_rows: int = 0
    asset_mutations: int = 0
    source_system: str = "connected_asset_platform"
    generated_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class MetricRange(BaseModel):
    min: float
    max: float
    unit: str | None = None


class ThresholdRange(BaseModel):
    normal: MetricRange | None = None
    warning: MetricRange | None = None
    critical: MetricRange | None = None
    min: float | None = None
    max: float | None = None
    unit: str | None = None


class EventTypeConfig(BaseModel):
    type: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    error_code: str | None = None


class CorruptionProfile(BaseModel):
    null_rate: float = 0.015
    duplicate_rate: float = 0.005
    invalid_numeric_rate: float = 0.002
    unknown_asset_rate: float = 0.001
    late_arrival_rate: float = 0.01
    out_of_order_rate: float = 0.02
    missing_field_rate: float = 0.005


class DomainConfig(BaseModel):
    domain: str
    asset_types: list[str]
    manufacturers: list[str]
    models: list[str] = Field(default_factory=list)
    metrics: dict[str, dict[str, ThresholdRange | MetricRange]] = Field(default_factory=dict)
    health_thresholds: dict[str, dict[str, float]] = Field(default_factory=dict)
    event_types: list[EventTypeConfig] = Field(default_factory=list)
    maintenance_types: list[str] = Field(default_factory=list)
    corruption_profile: CorruptionProfile = Field(default_factory=CorruptionProfile)


class GenerationConfig(BaseModel):
    seed: int = 42
    profile: Literal["small", "medium", "large"] = "medium"
    assets: int = 2000
    locations: int = 50
    operators: int = 500
    telemetry_interval_minutes: int = 5
    active_asset_ratio: float = 0.375
    history_days: int = 30
    corruption: CorruptionProfile = Field(default_factory=CorruptionProfile)

    def apply_profile(self) -> GenerationConfig:
        """Return a copy with profile-specific overrides applied."""
        overrides: dict[str, dict[str, int | float]] = {
            "small": {
                "assets": 50,
                "locations": 10,
                "operators": 20,
                "history_days": 7,
                "active_asset_ratio": 0.6,
            },
            "medium": {
                "assets": 2000,
                "locations": 50,
                "operators": 500,
                "history_days": 30,
                "active_asset_ratio": 0.375,
            },
            "large": {
                "assets": 10000,
                "locations": 200,
                "operators": 2000,
                "history_days": 90,
                "active_asset_ratio": 0.5,
            },
        }
        data = self.model_dump()
        data.update(overrides.get(self.profile, {}))
        return GenerationConfig(**data)


# Re-export constants for convenience in type hints / validation.
__all__ = [
    "ASSET_STATES",
    "DOMAINS",
    "SEVERITY_LEVELS",
    "Asset",
    "AssetState",
    "AssetType",
    "CorruptionProfile",
    "Domain",
    "DomainConfig",
    "EventRow",
    "EventTypeConfig",
    "GenerationBatch",
    "GenerationConfig",
    "Location",
    "MaintenanceRow",
    "MetricRange",
    "Operator",
    "TelemetryRow",
    "ThresholdRange",
]

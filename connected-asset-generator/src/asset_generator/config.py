"""Configuration loading for generation and domain YAML files."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from asset_generator.models import DomainConfig, GenerationConfig

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = PACKAGE_ROOT / "config"


class ConfigError(Exception):
    """Raised when configuration files are missing or invalid."""


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


@lru_cache(maxsize=1)
def load_generation_config(config_dir: Path | None = None) -> GenerationConfig:
    """Load and validate generation.yaml."""
    root = config_dir or Path(os.environ.get("ASSET_GENERATOR_CONFIG_DIR", DEFAULT_CONFIG_DIR))
    path = root / "generation.yaml"
    try:
        raw = _load_yaml(path)
        config = GenerationConfig(**raw)
        return config.apply_profile()
    except ValidationError as exc:
        raise ConfigError(f"Invalid generation config at {path}: {exc}") from exc


def load_domain_configs(config_dir: Path | None = None) -> dict[str, DomainConfig]:
    """Load all domain YAML files from config/domains/."""
    root = config_dir or Path(os.environ.get("ASSET_GENERATOR_CONFIG_DIR", DEFAULT_CONFIG_DIR))
    domains_dir = root / "domains"
    if not domains_dir.is_dir():
        raise ConfigError(f"Domain config directory not found: {domains_dir}")

    configs: dict[str, DomainConfig] = {}
    for path in sorted(domains_dir.glob("*.yaml")):
        try:
            raw = _load_yaml(path)
            domain = DomainConfig(**raw)
            configs[domain.domain] = domain
        except ValidationError as exc:
            raise ConfigError(f"Invalid domain config at {path}: {exc}") from exc

    if not configs:
        raise ConfigError(f"No domain configs found in {domains_dir}")
    return configs


def get_config_dir() -> Path:
    return Path(os.environ.get("ASSET_GENERATOR_CONFIG_DIR", DEFAULT_CONFIG_DIR))

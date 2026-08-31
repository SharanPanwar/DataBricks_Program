"""Smoke tests for Step 1 scaffold."""

from asset_generator import DOMAINS, DOMAIN_TELEMETRY_TABLES, __version__
from asset_generator.config import load_generation_config
from asset_generator.models import GenerationConfig


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_all_domains_have_telemetry_tables() -> None:
    assert set(DOMAIN_TELEMETRY_TABLES) == set(DOMAINS)


def test_generation_config_loads() -> None:
    config = load_generation_config()
    assert config.seed == 42
    assert config.profile == "medium"
    assert config.assets == 2000


def test_profile_overrides() -> None:
    small = GenerationConfig(profile="small").apply_profile()
    assert small.assets == 50
    assert small.history_days == 7

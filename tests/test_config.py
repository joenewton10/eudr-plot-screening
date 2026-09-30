import pytest

from eudr_screening.config import ConfigError, load_config

FIXTURES = "tests/fixtures"


def test_load_config_valid():
    config = load_config(f"{FIXTURES}/valid_config.yaml")

    assert config.operator.name == "Example Cocoa Cooperative Ltd"
    assert config.operator.reference == "OP-2026-000123"
    assert config.commodity == "cocoa"
    assert config.region == "Western North Region, Ghana"
    assert config.risk_thresholds.red_min_pct == 1.0
    assert config.risk_thresholds.amber_min_pct == 0.0
    assert config.dataset.forest_loss_source == "Hansen Global Forest Change v1.11 (2023 release)"
    assert config.input.results_csv == "data/eudr_screening_results.csv"
    assert config.output.report_path == "output/eudr_dds_report.pdf"


def test_load_config_missing_required_key_raises():
    with pytest.raises(ConfigError, match="region"):
        load_config(f"{FIXTURES}/missing_field_config.yaml")


def test_load_config_bad_threshold_order_raises():
    with pytest.raises(ConfigError, match="red_min_pct"):
        load_config(f"{FIXTURES}/bad_thresholds_config.yaml")


def test_load_config_non_numeric_threshold_raises():
    with pytest.raises(ConfigError, match="risk_thresholds"):
        load_config(f"{FIXTURES}/non_numeric_thresholds_config.yaml")

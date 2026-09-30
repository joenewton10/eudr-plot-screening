from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from eudr_screening.risk import RiskThresholds


class ConfigError(Exception):
    """Raised when config.yaml is missing required fields or has invalid values."""


@dataclass(frozen=True)
class OperatorInfo:
    name: str
    reference: str


@dataclass(frozen=True)
class DatasetInfo:
    forest_loss_source: str
    imagery_source: str


@dataclass(frozen=True)
class InputPaths:
    results_csv: str
    plots_geojson: str


@dataclass(frozen=True)
class OutputPaths:
    report_path: str


@dataclass(frozen=True)
class Config:
    operator: OperatorInfo
    commodity: str
    region: str
    cutoff_date: date
    risk_thresholds: RiskThresholds
    dataset: DatasetInfo
    input: InputPaths
    output: OutputPaths


_REQUIRED_TOP_LEVEL_KEYS = (
    "operator", "commodity", "region", "cutoff_date",
    "risk_thresholds", "dataset", "input", "output",
)


def _require_mapping(value, name: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"config.yaml {name} must be a mapping")
    return value


def load_config(path: str) -> Config:
    """Load and validate config.yaml into a Config."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"config.yaml is not valid YAML: {exc}") from exc

    raw = _require_mapping(raw, "must be a mapping of top-level keys (got an empty or invalid document)")

    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in raw:
            raise ConfigError(f"config.yaml is missing required key: {key!r}")

    operator_raw = _require_mapping(raw["operator"], "operator")
    for key in ("name", "reference"):
        if not operator_raw.get(key):
            raise ConfigError(f"config.yaml operator.{key} must be a non-empty string")

    thresholds_raw = _require_mapping(raw["risk_thresholds"], "risk_thresholds")
    for key in ("red_min_pct", "amber_min_pct"):
        if key not in thresholds_raw:
            raise ConfigError(f"config.yaml risk_thresholds is missing required key: {key!r}")
    try:
        red_min_pct = float(thresholds_raw["red_min_pct"])
        amber_min_pct = float(thresholds_raw["amber_min_pct"])
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"config.yaml risk_thresholds values must be numbers: {exc}") from exc

    if amber_min_pct < 0:
        raise ConfigError(f"risk_thresholds.amber_min_pct must be >= 0, got {amber_min_pct}")
    if red_min_pct <= amber_min_pct:
        raise ConfigError(
            "risk_thresholds.red_min_pct "
            f"({red_min_pct}) must be greater than amber_min_pct ({amber_min_pct})"
        )

    dataset_raw = _require_mapping(raw["dataset"], "dataset")
    for key in ("forest_loss_source", "imagery_source"):
        if not dataset_raw.get(key):
            raise ConfigError(f"config.yaml dataset.{key} must be a non-empty string")

    input_raw = _require_mapping(raw["input"], "input")
    for key in ("results_csv", "plots_geojson"):
        if not input_raw.get(key):
            raise ConfigError(f"config.yaml input.{key} must be a non-empty string")

    output_raw = _require_mapping(raw["output"], "output")
    if not output_raw.get("report_path"):
        raise ConfigError("config.yaml output.report_path must be a non-empty string")

    if not raw.get("commodity"):
        raise ConfigError("config.yaml commodity must be a non-empty string")
    if not raw.get("region"):
        raise ConfigError("config.yaml region must be a non-empty string")
    if not raw.get("cutoff_date"):
        raise ConfigError("config.yaml cutoff_date must be set")

    return Config(
        operator=OperatorInfo(name=operator_raw["name"], reference=operator_raw["reference"]),
        commodity=raw["commodity"],
        region=raw["region"],
        cutoff_date=raw["cutoff_date"],
        risk_thresholds=RiskThresholds(red_min_pct=red_min_pct, amber_min_pct=amber_min_pct),
        dataset=DatasetInfo(
            forest_loss_source=dataset_raw["forest_loss_source"],
            imagery_source=dataset_raw["imagery_source"],
        ),
        input=InputPaths(
            results_csv=input_raw["results_csv"],
            plots_geojson=input_raw["plots_geojson"],
        ),
        output=OutputPaths(report_path=output_raw["report_path"]),
    )

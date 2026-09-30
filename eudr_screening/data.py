import csv
import json
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry import shape

from eudr_screening.risk import RiskThresholds, classify_risk


@dataclass(frozen=True)
class PlotRecord:
    plot_id: int
    plot_area_ha: float
    loss_after_2020_ha: float
    loss_pct: float
    risk_flag_source: str
    risk_flag: str
    centroid_lon: float
    centroid_lat: float
    geometry: dict


@dataclass(frozen=True)
class ClassificationMismatch:
    plot_id: int
    loss_pct: float
    risk_flag_source: str
    risk_flag_computed: str


def _load_results_rows(results_csv_path: str) -> list[dict]:
    with open(results_csv_path, newline="") as f:
        return list(csv.DictReader(f))


def _load_geometries_by_plot_id(plots_geojson_path: str) -> dict[int, dict]:
    raw = json.loads(Path(plots_geojson_path).read_text())
    return {
        int(feature["properties"]["plot_id"]): feature["geometry"]
        for feature in raw["features"]
    }


def build_plot_records(
    results_csv_path: str,
    plots_geojson_path: str,
    thresholds: RiskThresholds,
) -> tuple[list[PlotRecord], list[ClassificationMismatch]]:
    rows = _load_results_rows(results_csv_path)
    geometries = _load_geometries_by_plot_id(plots_geojson_path)

    records = []
    mismatches = []
    for row in rows:
        plot_id = int(row["plot_id"])
        if plot_id not in geometries:
            raise ValueError(
                f"plot_id {plot_id} is in {results_csv_path} but has no matching "
                f"geometry in {plots_geojson_path}"
            )

        loss_pct = float(row["loss_pct"])
        risk_flag_source = row["risk_flag"]
        risk_flag = classify_risk(loss_pct, thresholds)

        if risk_flag != risk_flag_source:
            mismatches.append(
                ClassificationMismatch(
                    plot_id=plot_id,
                    loss_pct=loss_pct,
                    risk_flag_source=risk_flag_source,
                    risk_flag_computed=risk_flag,
                )
            )

        geometry = geometries[plot_id]
        centroid = shape(geometry).centroid

        records.append(
            PlotRecord(
                plot_id=plot_id,
                plot_area_ha=float(row["plot_area_ha"]),
                loss_after_2020_ha=float(row["loss_after_2020_ha"]),
                loss_pct=loss_pct,
                risk_flag_source=risk_flag_source,
                risk_flag=risk_flag,
                centroid_lon=centroid.x,
                centroid_lat=centroid.y,
                geometry=geometry,
            )
        )

    return records, mismatches

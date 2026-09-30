from datetime import date

from eudr_screening.config import Config, DatasetInfo, InputPaths, OperatorInfo, OutputPaths
from eudr_screening.data import ClassificationMismatch, PlotRecord
from eudr_screening.map import render_overview_map
from eudr_screening.report import build_report_context, render_pdf
from eudr_screening.risk import RiskThresholds

_CONFIG = Config(
    operator=OperatorInfo(name="Example Cocoa Cooperative Ltd", reference="OP-2026-000123"),
    commodity="cocoa",
    region="Western North Region, Ghana",
    cutoff_date=date(2020, 12, 31),
    risk_thresholds=RiskThresholds(red_min_pct=1.0, amber_min_pct=0.0),
    dataset=DatasetInfo(
        forest_loss_source="Hansen Global Forest Change v1.11 (2023 release)",
        imagery_source="Sentinel-2 SR Harmonized, 2024 composite",
    ),
    input=InputPaths(results_csv="data/eudr_screening_results.csv", plots_geojson="data/eudr_plots.geojson"),
    output=OutputPaths(report_path="output/eudr_dds_report.pdf"),
)


def _record(plot_id, risk_flag, plot_area_ha=10.0, loss_pct=0.0):
    return PlotRecord(
        plot_id=plot_id,
        plot_area_ha=plot_area_ha,
        loss_after_2020_ha=plot_area_ha * loss_pct / 100,
        loss_pct=loss_pct,
        risk_flag_source=risk_flag,
        risk_flag=risk_flag,
        centroid_lon=-2.55,
        centroid_lat=6.87,
        geometry={
            "type": "Polygon",
            "coordinates": [[[-2.55, 6.87], [-2.56, 6.87], [-2.56, 6.88], [-2.55, 6.87]]],
        },
    )


def test_build_report_context_summary_counts():
    records = [
        _record(1, "GREEN"),
        _record(2, "GREEN"),
        _record(3, "RED", loss_pct=12.0),
        _record(4, "AMBER", loss_pct=0.5),
    ]

    context = build_report_context(_CONFIG, records, mismatches=[])

    assert context["summary"]["GREEN"]["count"] == 2
    assert context["summary"]["RED"]["count"] == 1
    assert context["summary"]["AMBER"]["count"] == 1
    assert context["summary"]["GREEN"]["total_area_ha"] == 20.0


def test_build_report_context_requires_mitigation_is_red_only():
    records = [
        _record(1, "GREEN"),
        _record(2, "AMBER", loss_pct=0.5),
        _record(3, "RED", loss_pct=12.0),
        _record(4, "RED", loss_pct=8.0),
    ]

    context = build_report_context(_CONFIG, records, mismatches=[])

    assert context["requires_mitigation"] == [3, 4]


def test_build_report_context_passes_mismatches_through():
    records = [_record(1, "GREEN")]
    mismatches = [
        ClassificationMismatch(
            plot_id=1, loss_pct=0.0, risk_flag_source="RED", risk_flag_computed="GREEN"
        )
    ]

    context = build_report_context(_CONFIG, records, mismatches)

    assert context["mismatches"] == [
        {"plot_id": 1, "loss_pct": 0.0, "risk_flag_source": "RED", "risk_flag_computed": "GREEN"}
    ]


def test_render_pdf_writes_valid_pdf_file(tmp_path):
    records = [_record(1, "GREEN"), _record(3, "RED", loss_pct=12.0)]
    context = build_report_context(_CONFIG, records, mismatches=[])
    map_png = render_overview_map(records)
    output_path = tmp_path / "report.pdf"

    render_pdf(context, map_png, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 1000
    with open(output_path, "rb") as f:
        assert f.read(5) == b"%PDF-"

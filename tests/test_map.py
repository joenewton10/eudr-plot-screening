from eudr_screening.data import build_plot_records
from eudr_screening.map import render_overview_map
from eudr_screening.risk import RiskThresholds

DEFAULT_THRESHOLDS = RiskThresholds(red_min_pct=1.0, amber_min_pct=0.0)


def test_render_overview_map_produces_png_bytes():
    records, _ = build_plot_records(
        "data/eudr_screening_results.csv",
        "data/eudr_plots.geojson",
        DEFAULT_THRESHOLDS,
    )

    png_bytes = render_overview_map(records)

    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png_bytes) > 1000

import pytest

from eudr_screening.data import build_plot_records
from eudr_screening.risk import RiskThresholds

DEFAULT_THRESHOLDS = RiskThresholds(red_min_pct=1.0, amber_min_pct=0.0)


def test_build_plot_records_from_real_export():
    records, mismatches = build_plot_records(
        "data/eudr_screening_results.csv",
        "data/eudr_plots.geojson",
        DEFAULT_THRESHOLDS,
    )

    assert len(records) == 6
    assert mismatches == []

    by_id = {r.plot_id: r for r in records}
    assert by_id[1].risk_flag == "GREEN"
    assert by_id[4].risk_flag == "RED"

    # Plots sit in Western North Region, Ghana: roughly -2.7..-2.5 lon, 6.8..6.9 lat
    for record in records:
        assert -2.7 < record.centroid_lon < -2.5
        assert 6.8 < record.centroid_lat < 6.9


def test_build_plot_records_detects_classification_mismatch():
    records, mismatches = build_plot_records(
        "tests/fixtures/mismatched_results.csv",
        "data/eudr_plots.geojson",
        DEFAULT_THRESHOLDS,
    )

    assert len(mismatches) == 1
    mismatch = mismatches[0]
    assert mismatch.plot_id == 1
    assert mismatch.risk_flag_source == "RED"
    assert mismatch.risk_flag_computed == "GREEN"


def test_build_plot_records_raises_on_orphan_plot_id():
    with pytest.raises(ValueError, match="99"):
        build_plot_records(
            "tests/fixtures/orphan_plot_results.csv",
            "data/eudr_plots.geojson",
            DEFAULT_THRESHOLDS,
        )

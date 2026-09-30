import pytest

from eudr_screening.risk import RiskThresholds, classify_risk

DEFAULT_THRESHOLDS = RiskThresholds(red_min_pct=1.0, amber_min_pct=0.0)


@pytest.mark.parametrize(
    "loss_pct,expected",
    [
        (0.0, "GREEN"),
        (1.0, "AMBER"),          # exactly at red_min_pct stays in the lower band
        (1.0000001, "RED"),      # just above red_min_pct
        (0.0000001, "AMBER"),    # just above amber_min_pct
        (0.5, "AMBER"),
        (5.0, "RED"),
    ],
)
def test_classify_risk_boundaries(loss_pct, expected):
    assert classify_risk(loss_pct, DEFAULT_THRESHOLDS) == expected


@pytest.mark.parametrize(
    "loss_pct,expected",
    [
        (0.0, "GREEN"),                 # plot_id 1
        (0.0, "GREEN"),                 # plot_id 2
        (0.0, "GREEN"),                 # plot_id 3
        (12.7721303084218, "RED"),      # plot_id 4
        (51.641218656960305, "RED"),    # plot_id 5
        (13.369501174344157, "RED"),    # plot_id 6
    ],
)
def test_classify_risk_matches_real_export(loss_pct, expected):
    assert classify_risk(loss_pct, DEFAULT_THRESHOLDS) == expected


def test_classify_risk_uses_configured_thresholds_not_hardcoded():
    custom = RiskThresholds(red_min_pct=5.0, amber_min_pct=2.0)
    assert classify_risk(1.0, custom) == "GREEN"   # would be AMBER under defaults
    assert classify_risk(3.0, custom) == "AMBER"   # would be RED under defaults
    assert classify_risk(6.0, custom) == "RED"

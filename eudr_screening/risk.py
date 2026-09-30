from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    """Loss-percentage cutoffs that separate RED / AMBER / GREEN.

    loss_pct > red_min_pct                    -> RED
    amber_min_pct < loss_pct <= red_min_pct    -> AMBER
    loss_pct <= amber_min_pct                  -> GREEN
    """

    red_min_pct: float
    amber_min_pct: float


def classify_risk(loss_pct: float, thresholds: RiskThresholds) -> str:
    """Classify a plot's post-cutoff forest-loss percentage into a risk flag."""
    if loss_pct > thresholds.red_min_pct:
        return "RED"
    if loss_pct > thresholds.amber_min_pct:
        return "AMBER"
    return "GREEN"

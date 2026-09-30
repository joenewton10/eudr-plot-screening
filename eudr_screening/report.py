from datetime import datetime, timezone

from eudr_screening.config import Config
from eudr_screening.data import ClassificationMismatch, PlotRecord

_RISK_FLAGS = ("RED", "AMBER", "GREEN")


def build_report_context(
    config: Config,
    records: list[PlotRecord],
    mismatches: list[ClassificationMismatch],
) -> dict:
    """Build the plain-data context the PDF renderer needs. Pure and unit-testable."""
    summary = {
        flag: {
            "count": sum(1 for r in records if r.risk_flag == flag),
            "total_area_ha": sum(r.plot_area_ha for r in records if r.risk_flag == flag),
        }
        for flag in _RISK_FLAGS
    }

    rows = [
        {
            "plot_id": r.plot_id,
            "centroid_lat": r.centroid_lat,
            "centroid_lon": r.centroid_lon,
            "plot_area_ha": r.plot_area_ha,
            "loss_after_2020_ha": r.loss_after_2020_ha,
            "loss_pct": r.loss_pct,
            "risk_flag": r.risk_flag,
            "mitigation_required": r.risk_flag == "RED",
        }
        for r in records
    ]

    return {
        "operator_name": config.operator.name,
        "operator_reference": config.operator.reference,
        "commodity": config.commodity,
        "region": config.region,
        "cutoff_date": config.cutoff_date,
        "forest_loss_source": config.dataset.forest_loss_source,
        "imagery_source": config.dataset.imagery_source,
        "generated_at": datetime.now(timezone.utc),
        "summary": summary,
        "rows": rows,
        "requires_mitigation": [r.plot_id for r in records if r.risk_flag == "RED"],
        "mismatches": [
            {
                "plot_id": m.plot_id,
                "loss_pct": m.loss_pct,
                "risk_flag_source": m.risk_flag_source,
                "risk_flag_computed": m.risk_flag_computed,
            }
            for m in mismatches
        ],
    }

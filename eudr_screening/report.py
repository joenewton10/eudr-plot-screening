import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from eudr_screening.config import Config
from eudr_screening.data import ClassificationMismatch, PlotRecord

_RISK_FLAGS = ("RED", "AMBER", "GREEN")

_SCOPE_TEXT = (
    "This report screens the deforestation-risk status of the plots listed below "
    "against post-cutoff satellite-detected forest loss. It is a screening tool for "
    "the deforestation-risk question only — it does not assess legality or "
    "traceability, and it is not a legal Due Diligence Statement. It relies on a "
    "30 m global forest-loss dataset, which can miss sub-hectare clearance and can "
    "under- or over-count loss near plot edges. Cocoa agroforestry frequently reads "
    "as canopy cover from space, which is exactly why EUDR requires operator-supplied "
    "GPS polygons rather than remote farm detection: this report screens the polygon "
    "the operator provided, it does not find farms on its own."
)

_RISK_ROW_COLORS = {
    "RED": colors.HexColor("#f8d7da"),
    "AMBER": colors.HexColor("#fff3cd"),
    "GREEN": colors.HexColor("#d4edda"),
}


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


def _fit_within(
    max_width: float, max_height: float, natural_width: float, natural_height: float
) -> tuple[float, float]:
    """Scale (natural_width, natural_height) to fit within (max_width, max_height),
    preserving aspect ratio rather than stretching to fill the box."""
    scale = min(max_width / natural_width, max_height / natural_height)
    return natural_width * scale, natural_height * scale


def render_pdf(context: dict, map_png: bytes, output_path: str) -> None:
    """Render the report context and map image into a PDF at output_path."""
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []

    story.append(Paragraph("Due Diligence Statement — Deforestation Risk Screening", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Operator: {context['operator_name']} ({context['operator_reference']})", styles["Normal"]))
    story.append(Paragraph(f"Commodity: {context['commodity']}", styles["Normal"]))
    story.append(Paragraph(f"Region: {context['region']}", styles["Normal"]))
    story.append(Paragraph(f"Deforestation cutoff: {context['cutoff_date']}", styles["Normal"]))
    story.append(Paragraph(f"Forest-loss dataset: {context['forest_loss_source']}", styles["Normal"]))
    story.append(Paragraph(f"Imagery: {context['imagery_source']}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {context['generated_at'].isoformat()}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Scope and limitations", styles["Heading2"]))
    story.append(Paragraph(_SCOPE_TEXT, styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Summary", styles["Heading2"]))
    summary_data = [["Risk flag", "Plot count", "Total area (ha)"]]
    for flag in ("RED", "AMBER", "GREEN"):
        s = context["summary"][flag]
        summary_data.append([flag, str(s["count"]), f"{s['total_area_ha']:.2f}"])
    summary_table = Table(summary_data, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Plot overview map", styles["Heading2"]))
    map_width_px, map_height_px = ImageReader(io.BytesIO(map_png)).getSize()
    image_width, image_height = _fit_within(14 * cm, 14 * cm, map_width_px, map_height_px)
    story.append(Image(io.BytesIO(map_png), width=image_width, height=image_height))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Plot detail", styles["Heading2"]))
    plot_data = [["Plot ID", "Centroid (lat, lon)", "Area (ha)", "Loss (ha)", "Loss %", "Risk", "Mitigation"]]
    row_backgrounds = []
    for i, row in enumerate(context["rows"], start=1):
        plot_data.append([
            str(row["plot_id"]),
            f"{row['centroid_lat']:.4f}, {row['centroid_lon']:.4f}",
            f"{row['plot_area_ha']:.2f}",
            f"{row['loss_after_2020_ha']:.2f}",
            f"{row['loss_pct']:.2f}",
            row["risk_flag"],
            "Mitigation or exclusion required" if row["mitigation_required"] else "",
        ])
        row_backgrounds.append(("BACKGROUND", (0, i), (-1, i), _RISK_ROW_COLORS[row["risk_flag"]]))
    plot_table = Table(plot_data, hAlign="LEFT")
    plot_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        *row_backgrounds,
    ]))
    story.append(plot_table)

    if context["mismatches"]:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Data-integrity notices", styles["Heading2"]))
        story.append(Paragraph(
            "The following plots' recomputed risk classification does not match the "
            "classification in the source export. Investigate before relying on this report.",
            styles["Normal"],
        ))
        mismatch_data = [["Plot ID", "Loss %", "Source flag", "Recomputed flag"]]
        for m in context["mismatches"]:
            mismatch_data.append([
                str(m["plot_id"]), f"{m['loss_pct']:.2f}", m["risk_flag_source"], m["risk_flag_computed"]
            ])
        mismatch_table = Table(mismatch_data, hAlign="LEFT")
        mismatch_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(mismatch_table)

    doc.build(story)

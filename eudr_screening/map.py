import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from eudr_screening.data import PlotRecord

_RISK_COLORS = {"RED": "red", "AMBER": "orange", "GREEN": "green"}


def render_overview_map(records: list[PlotRecord]) -> bytes:
    """Render plot polygons colored by risk flag as a PNG, returned as bytes."""
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    for record in records:
        coords = record.geometry["coordinates"][0]
        color = _RISK_COLORS[record.risk_flag]
        polygon = Polygon(coords, closed=True, facecolor=color, edgecolor="black", alpha=0.6)
        ax.add_patch(polygon)
        ax.annotate(
            str(record.plot_id),
            (record.centroid_lon, record.centroid_lat),
            ha="center",
            va="center",
            fontsize=8,
        )

    lons = [pt[0] for record in records for pt in record.geometry["coordinates"][0]]
    lats = [pt[1] for record in records for pt in record.geometry["coordinates"][0]]
    lon_pad = (max(lons) - min(lons)) * 0.05 or 0.01
    lat_pad = (max(lats) - min(lats)) * 0.05 or 0.01
    ax.set_xlim(min(lons) - lon_pad, max(lons) + lon_pad)
    ax.set_ylim(min(lats) - lat_pad, max(lats) + lat_pad)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Plot risk overview")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()

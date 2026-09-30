import argparse
import sys
from pathlib import Path

from eudr_screening.config import ConfigError, load_config
from eudr_screening.data import build_plot_records
from eudr_screening.map import render_overview_map
from eudr_screening.report import build_report_context, render_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an EUDR plot-screening DDS-style report.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 2

    try:
        records, mismatches = build_plot_records(
            config.input.results_csv, config.input.plots_geojson, config.risk_thresholds
        )
    except FileNotFoundError as exc:
        print(f"Error loading input data: {exc}", file=sys.stderr)
        return 2

    if not records:
        print(f"No plots found in {config.input.results_csv}; nothing to report.", file=sys.stderr)
        return 2

    map_png = render_overview_map(records)
    context = build_report_context(config, records, mismatches)

    output_path = Path(config.output.report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(context, map_png, str(output_path))

    print(f"Screened {len(records)} plots:")
    for flag in ("RED", "AMBER", "GREEN"):
        s = context["summary"][flag]
        print(f"  {flag}: {s['count']} plots, {s['total_area_ha']:.2f} ha")
    if mismatches:
        print(f"WARNING: {len(mismatches)} plot(s) had a classification mismatch against the source export:")
        for m in mismatches:
            print(f"  plot {m.plot_id}: source={m.risk_flag_source} computed={m.risk_flag_computed}")
    print(f"Report written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

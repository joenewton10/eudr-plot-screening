# EUDR Plot-Level Deforestation Screening (cocoa, Ghana)

Repo name: `eudr-plot-screening`. This doc briefs the Python report side.

## What this is

The deforestation-screening half of an EUDR compliance tool. Google Earth Engine does
the geospatial work (done); Python turns the exported results into a
due-diligence-statement-style report. Same architecture as the Kakum project: GEE for
pixels, Python for the report, config-driven, tested.

## Where things stand

- GEE pipeline works: cocoa-district plots (Western North, Ghana) screened against
  post-2020 forest loss (Hansen `lossyear` >= 2021), each plot flagged RED / AMBER /
  GREEN.
- Exported from GEE:
  - `eudr_screening_results.csv`, one row per plot: `plot_id`, `plot_area_ha`,
    `loss_after_2020_ha`, `loss_pct`, `risk_flag`.
  - `eudr_plots.geojson`, the same plus geometry, for a map in the report.
- Commodity is cocoa for the demo, but the tool is commodity-agnostic (rubber, coffee,
  palm work by swapping the plot input). Keep `commodity` a config field, not baked
  into the logic.

## The regulation (what the report must reflect)

- EUDR applies from 30 December 2026 for large and medium operators (30 June 2027 for
  micro and small). Cocoa is one of the seven covered commodities. No further delay:
  the Commission confirmed the date and finalized the rules in 2026.
- Core test: a covered commodity must be produced on land NOT deforested after
  31 December 2020.
- Operators submit a Due Diligence Statement (DDS): geolocation of plots, a risk
  assessment result, and risk mitigation where risk is non-negligible.

## What to design (Python side)

- `config.yaml`: cutoff date, risk thresholds, commodity, operator reference, dataset
  versions.
- A module that reads the CSV, applies and verifies the risk classification, and
  generates a DDS-style PDF report: operator reference, commodity, per-plot geolocation
  and area and post-2020 loss and risk flag, and for any RED plot an explicit
  "mitigation or exclusion required" flag.
- Unit tests on the risk-classification function (pure logic, known inputs and
  outputs), the way the Kakum carbon maths was tested.
- No rasterio needed here (CSV in, PDF out), so the Smart App Control blocker from the
  Kakum side does not apply to this module.

## Honest scope (state in the README)

Screening tool for the deforestation-risk part only, not legality or traceability, and
not a legal DDS. Global datasets (Hansen 30 m) miss sub-hectare plots. Cocoa
agroforestry looks like forest from space, which is exactly why EUDR requires
operator-provided GPS polygons rather than remote farm detection. Name these limits;
they read as understanding, not weakness.

## How to start

Design first, do not jump to writing files. Talk through the report structure, the
risk-threshold rules, and the config schema, grounded in the real
`eudr_screening_results.csv`, before generating anything.

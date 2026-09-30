# EUDR Plot-Level Deforestation Screening (cocoa, Ghana)

Screens cocoa plots against post-2020 forest loss (Hansen Global Forest
Change) and produces a DDS-style PDF report per plot: risk flag, loss
area/percentage, and an explicit mitigation-or-exclusion flag for any RED
plot.

## Scope and limitations

This is a screening tool for the deforestation-risk question only. It is
**not** a legality or traceability check, and it is **not** a legal Due
Diligence Statement under EUDR. It relies on a 30 m global dataset (Hansen
Global Forest Change), which misses sub-hectare clearance and can
mis-measure loss near plot edges. Cocoa agroforestry frequently reads as
canopy cover from space — this is exactly why EUDR requires
operator-supplied GPS polygons rather than remote farm detection: this
tool screens the polygon an operator provides, it does not find farms on
its own.

## Usage

1. Install dependencies: `pip install -e ".[dev]"`
2. Edit `config.yaml` with the operator's details, and confirm the risk
   thresholds and input paths.
3. Run: `python -m eudr_screening.cli --config config.yaml`
4. The PDF report is written to the path set in `output.report_path`
   (`output/eudr_dds_report.pdf` by default).

## Tests

```
pytest
```

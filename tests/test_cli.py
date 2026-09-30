from eudr_screening.cli import main


def _write_config(tmp_path, output_path, results_csv="data/eudr_screening_results.csv", plots_geojson="data/eudr_plots.geojson"):
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text(
        f"""
operator:
  name: "Example Cocoa Cooperative Ltd"
  reference: "OP-2026-000123"
commodity: cocoa
region: "Western North Region, Ghana"
cutoff_date: 2020-12-31
risk_thresholds:
  red_min_pct: 1.0
  amber_min_pct: 0.0
dataset:
  forest_loss_source: "Hansen Global Forest Change v1.11 (2023 release)"
  imagery_source: "Sentinel-2 SR Harmonized, 2024 composite"
input:
  results_csv: "{results_csv}"
  plots_geojson: "{plots_geojson}"
output:
  report_path: "{output_path.as_posix()}"
"""
    )
    return config_yaml


def test_main_generates_report_from_real_data(tmp_path, capsys):
    output_path = tmp_path / "report.pdf"
    config_yaml = _write_config(tmp_path, output_path)

    exit_code = main(["--config", str(config_yaml)])

    assert exit_code == 0
    assert output_path.exists()
    captured = capsys.readouterr()
    assert "RED: 3 plots" in captured.out
    assert "GREEN: 3 plots" in captured.out


def test_main_returns_nonzero_on_missing_config(capsys):
    exit_code = main(["--config", "does/not/exist.yaml"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error loading config" in captured.err


def test_main_creates_missing_output_directory(tmp_path):
    output_path = tmp_path / "nested" / "dir" / "report.pdf"
    config_yaml = _write_config(tmp_path, output_path)

    exit_code = main(["--config", str(config_yaml)])

    assert exit_code == 0
    assert output_path.exists()


def test_main_returns_nonzero_on_missing_input_data(tmp_path, capsys):
    output_path = tmp_path / "report.pdf"
    config_yaml = _write_config(tmp_path, output_path, results_csv="does/not/exist.csv")

    exit_code = main(["--config", str(config_yaml)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error loading input data" in captured.err


def test_main_returns_nonzero_on_empty_results_csv(tmp_path, capsys):
    empty_csv = tmp_path / "empty_results.csv"
    empty_csv.write_text("plot_id,plot_area_ha,loss_after_2020_ha,loss_pct,risk_flag\n")
    output_path = tmp_path / "report.pdf"
    config_yaml = _write_config(tmp_path, output_path, results_csv=empty_csv.as_posix())

    exit_code = main(["--config", str(config_yaml)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "No plots found" in captured.err

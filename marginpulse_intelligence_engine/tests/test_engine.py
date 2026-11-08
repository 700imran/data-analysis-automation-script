from pathlib import Path
import pandas as pd
from marginpulse_engine.engine import analyze_paths, analyze_frames
from marginpulse_engine.mapping import map_dataset

ROOT = Path(__file__).resolve().parents[1]


def test_distributor_demo_runs_interconnected_modules(tmp_path):
    result = analyze_paths(
        [ROOT / "examples" / "distributor_demo.xlsx"],
        {"client_id": "dist-test", "profile": "distributor", "currency": "AED", "as_of_date": "2026-10-31"},
        tmp_path,
    )
    summary = result["summary"]
    assert summary["table_row_counts"]["sales"] == 1519
    assert summary["table_row_counts"]["receivables"] == 513
    assert result["ignored_sheets"] == []
    assert "sales_intelligence" in summary["available_modules"]
    assert "inventory_intelligence" in summary["available_modules"]
    assert "receivables_intelligence" in summary["available_modules"]
    assert "working_capital_intelligence" in summary["available_modules"]
    assert "reconciliation_intelligence" in summary["available_modules"]
    assert summary["reconciliation_status"] == "review_required"
    assert (Path(summary["output_directory"]) / "powerbi_export" / "kpis.csv").exists()
    assert list((Path(summary["output_directory"]) / "powerbi_export").glob("reconciliation_intelligence__details__*.csv"))
    assert Path(result["output_zip"]).exists()
    assert result["insights"]


def test_retailer_demo_activates_store_module(tmp_path):
    result = analyze_paths(
        [ROOT / "examples" / "retailer_demo.xlsx"],
        {"client_id": "retail-test", "profile": "retailer", "currency": "INR", "as_of_date": "2026-10-31"},
        tmp_path,
    )
    assert "retail_store_intelligence" in result["summary"]["available_modules"]
    assert result["module_results"]["retail_store_intelligence"]["store_count"] == 2
    assert result["summary"]["data_quality_status"] == "mapped"


def test_service_demo_activates_project_and_workforce_modules(tmp_path):
    result = analyze_paths(
        [ROOT / "examples" / "service_demo.xlsx"],
        {"client_id": "service-test", "profile": "service", "currency": "INR", "as_of_date": "2026-10-31"},
        tmp_path,
    )
    assert "service_project_intelligence" in result["summary"]["available_modules"]
    assert "workforce_utilisation" in result["summary"]["available_modules"]
    assert result["module_results"]["service_project_intelligence"]["project_margin_total"] == 31000.0


def test_missing_cost_is_not_silently_zero():
    source = pd.DataFrame({"Invoice Date": ["2026-10-01"], "Net Sales": [100], "Qty": [2]})
    mapped, qa = map_dataset(source, "sales")
    assert "revenue" in mapped.columns
    assert "cogs" not in mapped.columns
    assert qa["status"] == "ready"
    assert mapped["revenue"].iloc[0] == 100


def test_column_mapping_override_for_custom_schema(tmp_path):
    source = pd.DataFrame({"Transacted On": ["2026-10-01"], "Business Value": [1234], "Account Ref": ["C1"]})
    result = analyze_frames(
        [("strange_export.csv", [("strange_export", source)])],
        {
            "client_id": "custom-map", "profile": "auto", "currency": "INR", "as_of_date": "2026-10-31",
            "dataset_map": {"strange_export": "sales"},
            "column_mappings": {"sales": {"transaction_date": "Transacted On", "revenue": "Business Value", "customer_id": "Account Ref"}},
        }, tmp_path,
    )
    assert result["summary"]["table_row_counts"]["sales"] == 1
    assert "sales_intelligence" in result["summary"]["available_modules"]


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



# --- Regression tests added after accuracy review (v0.1.1) ---
def _distributor_result(tmp_path):
    import json
    cfg = json.load(open(Path(__file__).resolve().parents[1] / "examples" / "distributor_config.json"))
    return analyze_paths([Path(__file__).resolve().parents[1] / "examples" / "distributor_demo.xlsx"], cfg, tmp_path)


def test_all_caps_headers_map_and_cogs_uses_source_column(tmp_path):
    result = _distributor_result(tmp_path)
    kpis = result["module_results"]["financial_performance"]["kpis"]
    # Independent totals computed directly from the demo workbook.
    assert kpis["revenue_total"] == 364777.34
    assert kpis["cogs_total"] == 250121.29
    assert abs(kpis["gross_profit_total"] - 114656.05) < 0.01
    checks = {c["check"]: c for c in result["module_results"]["reconciliation_intelligence"]["checks"]}
    assert checks["source_gross_profit_vs_recalculated"]["status"] == "passed"


def test_negative_stock_is_flagged_not_called_reorder(tmp_path):
    result = _distributor_result(tmp_path)
    inv = result["module_results"]["inventory_intelligence"]
    assert inv["items_negative_stock"] == 4
    assert inv["items_below_reorder"] == 0
    ids = {i["insight_id"] for i in result["insights"]}
    assert "INV_NEG_001" in ids and "INV_LOW_001" not in ids


def test_price_increase_is_not_a_supplier_mix_artefact(tmp_path):
    result = _distributor_result(tmp_path)
    assert "PROC_PRICE_001" not in {i["insight_id"] for i in result["insights"]}


def test_ageing_matches_independent_calculation(tmp_path):
    ar = _distributor_result(tmp_path)["module_results"]["receivables_intelligence"]
    assert ar["outstanding_total"] == 122848.51
    assert ar["overdue_total"] == 110833.96


def test_dayfirst_dates_and_duplicate_warning(tmp_path):
    import pandas as pd
    df = pd.DataFrame({"Bill Date": ["05/10/2026", "05/10/2026", "11/10/2026"], "Bill No": ["B2", "B2", "B3"], "Amount": [100, 100, 50], "Cost": [60, 60, 30]})
    f = tmp_path / "sales.csv"
    df.to_csv(f, index=False)
    result = analyze_paths([f], {"client_id": "t", "as_of_date": "2026-10-31", "dataset_map": {"sales.csv": "sales"}}, tmp_path / "o")
    assert [m["period"] for m in result["module_results"]["financial_performance"]["monthly_performance"]] == ["2026-10"]
    assert "DQ_DUP_001" in {i["insight_id"] for i in result["insights"]}


def test_indian_tally_style_headers_map_and_tie_to_source(tmp_path):
    import json
    import pandas as pd
    base = Path(__file__).resolve().parents[1] / "examples"
    cfg = json.load(open(base / "indian_distributor_config.json"))
    result = analyze_paths([base / "indian_distributor_demo.xlsx"], cfg, tmp_path)
    # Every dataset resolves its required fields from Voucher/Party/Item/Taxable style headers.
    assert all(not d["missing_required_fields"] for d in result["data_quality"])
    sales = pd.read_excel(base / "indian_distributor_demo.xlsx", "Sales")
    kpis = result["module_results"]["financial_performance"]["kpis"]
    assert abs(kpis["revenue_total"] - round(sales.TaxableValue.sum(), 2)) < 0.01   # taxable value, GST excluded
    checks = {c["check"]: c["status"] for c in result["module_results"]["reconciliation_intelligence"]["checks"]}
    assert set(checks.values()) == {"passed"}        # GST-inclusive receivables reconcile to sales + GST
    ids = [i["insight_id"] for i in result["insights"]]
    assert "AR_CUST_001" in ids and "DQ_DUP_001" not in ids
    assert "DQ_REQUIRED_001" not in ids and "DQ_DERIVED_REV_001" not in ids


def test_unmapped_required_fields_are_reported_loudly(tmp_path):
    import pandas as pd
    df = pd.DataFrame({"Doc": ["A1", "A2"], "Dt": ["2026-10-01", "2026-10-02"], "Qty": [1, 2], "Rate": [100, 100], "Weird Discount": [5, 5]})
    f = tmp_path / "s.csv"; df.to_csv(f, index=False)
    result = analyze_paths([f], {"client_id": "t", "as_of_date": "2026-10-31", "dataset_map": {"s.csv": "sales"}}, tmp_path / "o")
    ids = {i["insight_id"] for i in result["insights"]}
    assert "DQ_REQUIRED_001" in ids and "DQ_DERIVED_REV_001" in ids

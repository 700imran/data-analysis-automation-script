from __future__ import annotations
import json, uuid, shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd
from .io import detect_dataset, load_local_file, build_output_zip, write_json, slug
from .mapping import map_dataset
from .analysis import (
    calculate_financial_performance, calculate_sales_intelligence, calculate_cost_intelligence,
    calculate_inventory, calculate_ageing, calculate_procurement, calculate_retail_store,
    calculate_service_projects, calculate_product_profitability, calculate_working_capital,
    calculate_collections, calculate_reconciliations, module_availability, build_insights,
)
from .registry import PROFILES

ENGINE_VERSION = "0.1.1"


def _dataset_from_frame(file_name: str, sheet_name: str, config: dict) -> str | None:
    dataset_map = config.get("dataset_map", {}) or {}
    keys = [f"{file_name}::{sheet_name}", sheet_name, file_name]
    for key in keys:
        if key in dataset_map:
            return dataset_map[key]
    return detect_dataset(sheet_name) or detect_dataset(file_name)


def _collect_frames(files: list[tuple[str, list[tuple[str, pd.DataFrame]]]], config: dict) -> tuple[dict, list, list]:
    collected: dict[str, list[pd.DataFrame]] = {}
    quality: list[dict] = []
    ignored: list[dict] = []
    overrides = config.get("column_mappings", {}) or {}
    for file_name, sheets in files:
        for sheet_name, frame in sheets:
            if frame is None or frame.empty or frame.dropna(how="all").empty:
                continue
            if slug(sheet_name) in {"readme", "data_dictionary", "dictionary", "metadata", "notes"}:
                continue
            dataset = _dataset_from_frame(file_name, sheet_name, config)
            if not dataset:
                ignored.append({"file": file_name, "sheet": sheet_name, "reason": "Dataset type not recognised. Add it to dataset_map in client config."})
                continue
            mapped, qa = map_dataset(frame, dataset, overrides.get(dataset, {}), dayfirst=bool(config.get("dayfirst", True)))
            qa["source_file"] = file_name
            qa["source_sheet"] = sheet_name
            quality.append(qa)
            if not mapped.empty:
                collected.setdefault(dataset, []).append(mapped)
    tables = {name: pd.concat(frames, ignore_index=True, sort=False) for name, frames in collected.items()}
    return tables, quality, ignored


def _save_outputs(
    output_dir: Path,
    client_id: str,
    profile: str,
    currency: str,
    as_of: pd.Timestamp,
    tables: dict[str, pd.DataFrame],
    data_quality: list[dict],
    ignored_sheets: list[dict],
    modules: list[dict],
    module_results: dict,
    insights: list[dict],
    config: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir = output_dir / "normalized_data"
    pbi_dir = output_dir / "powerbi_export"
    normalized_dir.mkdir(exist_ok=True)
    pbi_dir.mkdir(exist_ok=True)

    for name, df in tables.items():
        df.to_csv(normalized_dir / f"{name}.csv", index=False)

    # Export a derived stock snapshot as a canonical table when only movements were uploaded.
    if "inventory_snapshot" not in tables and "inventory_intelligence" in module_results:
        details = module_results["inventory_intelligence"].get("product_detail", [])
        if details:
            pd.DataFrame(details).to_csv(normalized_dir / "derived_inventory_snapshot.csv", index=False)

    pd.DataFrame(modules).to_csv(pbi_dir / "module_availability.csv", index=False)
    pd.DataFrame(data_quality).to_csv(pbi_dir / "data_quality.csv", index=False)
    pd.DataFrame(insights).to_csv(pbi_dir / "insights.csv", index=False)
    kpi_rows = []
    for module, payload in module_results.items():
        for metric, value in payload.get("kpis", {}).items():
            if isinstance(value, (int, float)) or value is None:
                kpi_rows.append({"module": module, "metric": metric, "value": value, "currency": currency})
        for metric, value in payload.items():
            if metric.endswith("_total") or metric in {"total_revenue", "gross_margin_pct", "total_expenses", "outstanding_total", "overdue_total", "overdue_share_pct", "purchase_value_total", "indicative_inventory_value", "project_revenue_total", "project_cost_total", "project_margin_total", "billable_utilisation_pct"}:
                if isinstance(value, (int, float)) or value is None:
                    kpi_rows.append({"module": module, "metric": metric, "value": value, "currency": currency})
    pd.DataFrame(kpi_rows, columns=["module", "metric", "value", "currency"]).to_csv(pbi_dir / "kpis.csv", index=False)
    monthly = module_results.get("financial_performance", {}).get("monthly_performance", [])
    if monthly:
        pd.DataFrame(monthly).to_csv(pbi_dir / "monthly_performance.csv", index=False)
    for module, payload in module_results.items():
        for key, value in payload.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                pd.DataFrame(value).to_csv(pbi_dir / f"{module}__{slug(key)}.csv", index=False)
            elif isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, list) and nested_value and isinstance(nested_value[0], dict):
                        pd.DataFrame(nested_value).to_csv(pbi_dir / f"{module}__{slug(key)}__{slug(nested_key)}.csv", index=False)

    manifest = {
        "engine": "MarginPulse Configurable Business Intelligence Engine",
        "engine_version": ENGINE_VERSION,
        "analysis_id": output_dir.name,
        "client_id": client_id,
        "profile": profile,
        "currency": currency,
        "as_of_date": str(as_of.date()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "input_files_are_not_included": True,
        "limitations": [
            "Outputs are analytical support, not audited financial statements or guaranteed recommendations.",
            "Metrics depend on completeness, consistency, accounting basis and mapping of supplied data.",
            "Only modules marked available should be used for client-facing conclusions.",
        ],
    }
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "analysis.json", {
        "manifest": manifest,
        "module_availability": modules,
        "module_results": module_results,
        "insights": insights,
        "data_quality": data_quality,
        "ignored_sheets": ignored_sheets,
        "table_row_counts": {k: int(len(v)) for k, v in tables.items()},
        "client_configuration": {k: v for k, v in config.items() if k not in {"api_key", "secret", "password"}},
    })
    (pbi_dir / "README_POWERBI.txt").write_text(
        "Import the CSV files in this folder and normalized_data as separate tables.\n"
        "Use the model guide in docs/POWER_BI_MODEL.md for suggested relationships.\n"
        "Keep each client's exported files in a separate workspace/folder.\n",
        encoding="utf-8",
    )


def analyze_frames(
    files: list[tuple[str, list[tuple[str, pd.DataFrame]]]],
    config: dict | None = None,
    output_root: str | Path = "./storage",
    analysis_id: str | None = None,
) -> dict:
    config = config or {}
    client_id = slug(config.get("client_id", "demo_client")) or "demo_client"
    profile = str(config.get("profile", "auto")).lower()
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile '{profile}'. Choose from: {', '.join(PROFILES)}")
    country = str(config.get("country") or "India")
    currency = str(config.get("currency") or ("INR" if country.lower() == "india" else "AED")).upper()
    as_of = pd.Timestamp(config.get("as_of_date", date.today()))
    if pd.isna(as_of):
        raise ValueError("as_of_date must be a valid date, e.g. 2026-10-31")
    tables, data_quality, ignored = _collect_frames(files, config)
    if not tables:
        raise ValueError("No recognised datasets were received. Name files/sheets (e.g. Sales, Expenses) or provide dataset_map.")

    # Add canonical product/customer/supplier descriptions to transaction tables only when keys align.
    for transaction_dataset, dimension_dataset, key, name_field in [
        ("sales", "products", "product_id", "product_name"),
        ("purchases", "products", "product_id", "product_name"),
        ("sales", "customers", "customer_id", "customer_name"),
        ("receivables", "customers", "customer_id", "customer_name"),
        ("purchases", "suppliers", "supplier_id", "supplier_name"),
        ("payables", "suppliers", "supplier_id", "supplier_name"),
    ]:
        tx, dim = tables.get(transaction_dataset), tables.get(dimension_dataset)
        if tx is not None and dim is not None and key in tx.columns and key in dim.columns and name_field in dim.columns:
            lookup = dim.dropna(subset=[key]).drop_duplicates(key).set_index(key)[name_field]
            if name_field not in tx.columns:
                tx[name_field] = tx[key].map(lookup)
            else:
                tx[name_field] = tx[name_field].where(tx[name_field].notna(), tx[key].map(lookup))

    # Use one as-of date and one currency for all derived calculations; no FX conversion is performed.
    module_results: dict[str, dict] = {}
    financial = calculate_financial_performance(tables)
    if financial:
        module_results["financial_performance"] = financial
    sales = calculate_sales_intelligence(tables)
    if sales:
        module_results["sales_intelligence"] = sales
    product_profitability = calculate_product_profitability(tables)
    if product_profitability:
        module_results["product_profitability"] = product_profitability
    costs = calculate_cost_intelligence(tables)
    if costs:
        module_results["cost_intelligence"] = costs
    # Inventory snapshot can be derived from movements when necessary.
    from .analysis import derive_inventory_snapshot
    derived_snapshot = derive_inventory_snapshot(tables, as_of)
    if not derived_snapshot.empty and "inventory_snapshot" not in tables:
        tables["inventory_snapshot"] = derived_snapshot
    inventory = calculate_inventory(tables, as_of)
    if inventory:
        module_results["inventory_intelligence"] = inventory
    movements = tables.get("inventory_movements", pd.DataFrame())
    if not movements.empty and "quantity_delta" in movements.columns:
        module_results["inventory_movement_intelligence"] = {
            "movement_rows": int(len(movements)),
            "net_quantity_change": float(pd.to_numeric(movements["quantity_delta"], errors="coerce").sum(min_count=1)) if pd.to_numeric(movements["quantity_delta"], errors="coerce").notna().any() else None,
        }
    ar = calculate_ageing(tables.get("receivables", pd.DataFrame()), as_of, "customer_name" if "customer_name" in tables.get("receivables", pd.DataFrame()).columns else "customer_id")
    if ar:
        module_results["receivables_intelligence"] = ar
    ap = calculate_ageing(tables.get("payables", pd.DataFrame()), as_of, "supplier_name" if "supplier_name" in tables.get("payables", pd.DataFrame()).columns else "supplier_id")
    if ap:
        module_results["payables_intelligence"] = ap
    working_capital = calculate_working_capital(tables, inventory, ar, ap)
    if working_capital:
        module_results["working_capital_intelligence"] = working_capital
    collections = calculate_collections(tables)
    if collections:
        module_results["collections_intelligence"] = collections
    reconciliations = calculate_reconciliations(tables)
    if reconciliations:
        module_results["reconciliation_intelligence"] = reconciliations
    procurement = calculate_procurement(tables)
    if procurement:
        module_results["procurement_intelligence"] = procurement
    retail = calculate_retail_store(tables)
    if retail:
        module_results["retail_store_intelligence"] = retail
    service = calculate_service_projects(tables)
    if service:
        module_results["service_project_intelligence"] = service
    if "timesheets" in tables and not tables["timesheets"].empty and "hours_total" in service:
        module_results["workforce_utilisation"] = {k: service[k] for k in ["hours_total", "billable_utilisation_pct", "timesheet_rows"] if k in service}

    modules = module_availability(tables, profile)
    # Mark modules as available only when their calculation actually ran. Data existence alone is not enough.
    for item in modules:
        if item["available"] and item["module"] not in module_results:
            item["available"] = False
            item["reason"] = "Required data exists but this module could not calculate a valid result. Review data quality."
    insights = build_insights(tables, module_results, as_of, config.get("thresholds", {}))
    for qa in data_quality:
        missing_req = qa.get("missing_required_fields") or []
        if missing_req:
            insights.insert(0, {"insight_id": "DQ_REQUIRED_001", "severity": "high", "title": "Required fields not mapped", "finding": f"{qa.get('dataset')} ({qa.get('source_sheet')}) has no mapped column for: {', '.join(missing_req)}. Analyses that depend on them (for example monthly trends or joins) are unavailable or incomplete.", "evidence": {"dataset": qa.get("dataset"), "missing_required_fields": missing_req, "unmapped_source_columns": qa.get("unmapped_source_columns", [])}, "recommended_action": "Map the correct source columns in the client config (column_mappings) and re-run before using any result.", "limitation": "Automatic header matching cannot recognise every naming convention."})
        rev_src = str((qa.get("mapped_fields") or {}).get("revenue", ""))
        if rev_src.startswith("<derived"):
            hints = [c for c in qa.get("unmapped_source_columns", []) if any(k in str(c).lower() for k in ("disc", "tax", "net", "amount", "value"))]
            insights.insert(0, {"insight_id": "DQ_DERIVED_REV_001", "severity": "high", "title": "Revenue was derived, not read from the source", "finding": f"{qa.get('dataset')} revenue was calculated as {rev_src}. Source columns that may hold the real figure were not used: {', '.join(map(str, hints)) or 'none identified'}.", "evidence": {"dataset": qa.get("dataset"), "revenue_source": rev_src, "candidate_unmapped_columns": hints}, "recommended_action": "Confirm which column is net revenue and map it explicitly; a derived figure can differ from the books (for example if discounts or taxes are handled in other columns).", "limitation": "Derived revenue is only as complete as the columns the engine could recognise."})
        dups = int(qa.get("duplicate_rows", 0) or 0)
        if dups > 0:
            insights.append({"insight_id": "DQ_DUP_001", "severity": "medium", "title": "Duplicate rows detected", "finding": f"{dups} fully duplicated rows were found in {qa.get('source_sheet') or qa.get('dataset')} ({qa.get('dataset')}). They are NOT removed, so totals include them.", "evidence": {"dataset": qa.get("dataset"), "source_file": qa.get("source_file"), "source_sheet": qa.get("source_sheet"), "duplicate_rows": dups}, "recommended_action": "Confirm with the client whether these are genuine repeated lines or double-exported records, then re-run on corrected data.", "limitation": "Identical rows can be legitimate (e.g. repeated identical purchases); the engine does not delete or adjust source records automatically."})

    analysis_id = analysis_id or uuid.uuid4().hex[:12]
    client_root = Path(output_root).resolve() / client_id
    output_dir = client_root / analysis_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_outputs(output_dir, client_id, profile, currency, as_of, tables, data_quality, ignored, modules, module_results, insights, config)
    zip_path = client_root / f"{analysis_id}.zip"
    build_output_zip(output_dir, zip_path)

    reconciliation_review = any(check.get("status") == "review" for check in reconciliations.get("checks", []))
    quality_review = any(q["status"] != "ready" for q in data_quality) or reconciliation_review or bool(ignored)
    summary = {
        "analysis_id": analysis_id,
        "client_id": client_id,
        "profile": profile,
        "currency": currency,
        "as_of_date": str(as_of.date()),
        "datasets_detected": sorted(tables.keys()),
        "table_row_counts": {k: int(len(v)) for k, v in tables.items()},
        "available_modules": [x["module"] for x in modules if x["available"]],
        "unavailable_modules": [x for x in modules if not x["available"]],
        "insight_count": len(insights),
        "data_quality_status": "review_required" if quality_review else "mapped",
        "reconciliation_status": "review_required" if reconciliation_review else ("passed" if reconciliations else "not_run"),
        "output_directory": str(output_dir),
        "download_path": str(zip_path),
    }
    return {"summary": summary, "module_availability": modules, "module_results": module_results, "insights": insights, "data_quality": data_quality, "ignored_sheets": ignored, "output_zip": str(zip_path)}


def analyze_paths(paths: list[str | Path], config: dict | None = None, output_root: str | Path = "./storage") -> dict:
    files = []
    for path in paths:
        p = Path(path)
        files.append((p.name, load_local_file(p)))
    return analyze_frames(files, config=config, output_root=output_root)

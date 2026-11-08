from __future__ import annotations
import re
from typing import Any
import pandas as pd
from .registry import FIELD_ALIASES, REQUIRED_FIELDS


def normalize_name(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype("string").str.replace(",", "", regex=False).str.replace(r"^\((.*)\)$", r"-\1", regex=True).str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def map_dataset(df: pd.DataFrame, dataset: str, overrides: dict[str, str] | None = None) -> tuple[pd.DataFrame, dict]:
    if dataset not in FIELD_ALIASES:
        raise ValueError(f"Unknown dataset type: {dataset}")
    source = df.copy()
    source.columns = [str(c).strip() for c in source.columns]
    normalized_lookup = {normalize_name(c): c for c in source.columns}
    aliases = FIELD_ALIASES[dataset]
    overrides = overrides or {}
    mapping: dict[str, str] = {}
    for canonical, alias_list in aliases.items():
        requested = overrides.get(canonical)
        if requested and requested in source.columns:
            mapping[canonical] = requested
            continue
        candidates = [canonical] + alias_list
        for candidate in candidates:
            key = normalize_name(candidate)
            if key in normalized_lookup:
                mapping[canonical] = normalized_lookup[key]
                break
    out = pd.DataFrame(index=source.index)
    for canonical, original in mapping.items():
        out[canonical] = source[original]
    # Parse dates and numeric-like fields but preserve missing values; never fill unknown finance values with zero.
    date_fields = {"transaction_date", "invoice_date", "due_date", "snapshot_date", "last_sale_date", "start_date", "end_date", "work_date"}
    numeric_fields = {
        "quantity", "unit_price", "discount", "revenue", "unit_cost", "cogs", "gross_profit", "quantity_returned", "return_amount", "purchase_value", "amount", "quantity_delta", "opening_quantity", "received_quantity", "sold_quantity", "adjustment_quantity", "closing_quantity", "reorder_level", "inventory_value", "days_since_last_sale", "invoice_amount", "paid_amount", "outstanding_amount", "credit_limit", "payment_terms_days", "selling_price", "project_revenue", "project_cost", "hours", "billable_hours", "hourly_cost", "billable_amount"
    }
    for col in out.columns:
        if col in date_fields:
            out[col] = pd.to_datetime(out[col], errors="coerce", dayfirst=False)
        elif col in numeric_fields:
            out[col] = _numeric(out[col])
        elif out[col].dtype == "object":
            out[col] = out[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    # Safe derived monetary fields only when their components are present.
    if dataset == "sales":
        if "revenue" not in out.columns and {"quantity", "unit_price"}.issubset(out.columns):
            gross = out["quantity"] * out["unit_price"]
            out["revenue"] = gross - out.get("discount", 0).fillna(0) if isinstance(out.get("discount", 0), pd.Series) else gross
            mapping["revenue"] = "<derived: quantity * unit_price - discount>"
        if "cogs" not in out.columns and {"quantity", "unit_cost"}.issubset(out.columns):
            out["cogs"] = out["quantity"] * out["unit_cost"]
            mapping["cogs"] = "<derived: quantity * unit_cost>"
        if "gross_profit" not in out.columns and {"revenue", "cogs"}.issubset(out.columns):
            out["gross_profit"] = out["revenue"] - out["cogs"]
            mapping["gross_profit"] = "<derived: revenue - cogs>"
    if dataset in {"receivables", "payables"} and "outstanding_amount" not in out.columns and {"invoice_amount", "paid_amount"}.issubset(out.columns):
        out["outstanding_amount"] = out["invoice_amount"] - out["paid_amount"]
        mapping["outstanding_amount"] = "<derived: invoice_amount - paid_amount>"
    out = out.dropna(how="all").copy()
    required = REQUIRED_FIELDS.get(dataset, [])
    missing_required = [f for f in required if f not in out.columns or out[f].isna().all()]
    required_missing_counts = {f: int(out[f].isna().sum()) for f in required if f in out.columns and out[f].isna().any()}
    required_all_null = [f for f in required if f not in out.columns or out[f].isna().all()]
    status = "incomplete" if required_all_null else ("review" if required_missing_counts else "ready")
    quality = {
        "dataset": dataset,
        "source_columns": list(source.columns),
        "mapped_fields": mapping,
        "unmapped_source_columns": [c for c in source.columns if c not in mapping.values() and c not in [v for v in mapping.values() if str(v).startswith("<derived:")]],
        "row_count": int(len(out)),
        "missing_required_fields": required_all_null,
        "missing_required_value_counts": required_missing_counts,
        "missing_values_by_field": {c: int(out[c].isna().sum()) for c in out.columns if out[c].isna().any()},
        "duplicate_rows": int(out.duplicated().sum()),
        "status": status,
    }
    return out, quality

from __future__ import annotations
from datetime import date
from typing import Any
import numpy as np
import pandas as pd
from .registry import MODULES


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def _money(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def _records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    copy = df.copy()
    for col in copy.columns:
        if pd.api.types.is_datetime64_any_dtype(copy[col]):
            copy[col] = copy[col].dt.strftime("%Y-%m-%d")
    return copy.replace({np.nan: None}).to_dict(orient="records")


def derive_inventory_snapshot(tables: dict[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    snapshot = tables.get("inventory_snapshot", pd.DataFrame()).copy()
    if not snapshot.empty:
        if "snapshot_date" not in snapshot.columns:
            snapshot["snapshot_date"] = as_of
        return snapshot
    movements = tables.get("inventory_movements", pd.DataFrame()).copy()
    if movements.empty or not {"product_id", "quantity_delta"}.issubset(movements.columns):
        return pd.DataFrame()
    if "transaction_date" in movements.columns:
        movements = movements.sort_values("transaction_date")
    movements["quantity_delta"] = _num(movements, "quantity_delta")
    grouped = movements.groupby("product_id", dropna=False)
    result = grouped.agg(closing_quantity=("quantity_delta", "sum")).reset_index()
    name_cols = [c for c in ["product_name"] if c in movements.columns]
    if name_cols:
        names = movements.dropna(subset=name_cols).drop_duplicates("product_id").set_index("product_id")[name_cols[0]]
        result["product_name"] = result["product_id"].map(names)
    if "unit_cost" in movements.columns:
        costs = movements.dropna(subset=["unit_cost"]).groupby("product_id")["unit_cost"].last()
        result["unit_cost"] = result["product_id"].map(costs)
        result["inventory_value"] = result["closing_quantity"] * result["unit_cost"]
    result["snapshot_date"] = as_of
    if "transaction_date" in movements.columns and "movement_type" in movements.columns:
        sales_moves = movements[movements["movement_type"].astype(str).str.lower().str.contains("sale|issue|out", na=False)]
        if not sales_moves.empty:
            last_sales = sales_moves.groupby("product_id")["transaction_date"].max()
            result["last_sale_date"] = result["product_id"].map(last_sales)
            result["days_since_last_sale"] = (as_of - pd.to_datetime(result["last_sale_date"], errors="coerce")).dt.days
    return result


def calculate_financial_performance(tables: dict[str, pd.DataFrame]) -> dict:
    sales = tables.get("sales", pd.DataFrame()).copy()
    expenses = tables.get("expenses", pd.DataFrame()).copy()
    if sales.empty and expenses.empty:
        return {}
    kpis: dict[str, Any] = {}
    monthly = pd.DataFrame()
    if not sales.empty:
        if "revenue" in sales.columns:
            revenue = _num(sales, "revenue")
            kpis["revenue_total"] = _money(revenue.sum(min_count=1))
        else:
            revenue = pd.Series(dtype=float)
        if "cogs" in sales.columns and "revenue" in sales.columns:
            cogs = _num(sales, "cogs")
            gross_profit = revenue - cogs
            valid = revenue.notna() & cogs.notna()
            kpis["cogs_total"] = _money(cogs.sum(min_count=1))
            kpis["gross_profit_total"] = _money(gross_profit[valid].sum() if valid.any() else None)
            denominator = revenue[valid].sum()
            kpis["gross_margin_pct"] = round(float(gross_profit[valid].sum() / denominator * 100), 2) if denominator else None
            kpis["gross_profit_data_coverage_pct"] = round(float(valid.mean() * 100), 2) if len(valid) else 0.0
        if "transaction_date" in sales.columns and "revenue" in sales.columns:
            s = sales.dropna(subset=["transaction_date"]).copy()
            s["period"] = pd.to_datetime(s["transaction_date"]).dt.to_period("M").astype(str)
            monthly = s.groupby("period", as_index=False).agg(
                revenue=("revenue", lambda x: x.sum(min_count=1)),
                revenue_rows=("revenue", "count"),
                sales_rows=("revenue", "size"),
            )
            monthly["revenue_coverage_pct"] = np.where(monthly["sales_rows"] > 0, monthly["revenue_rows"] / monthly["sales_rows"] * 100, np.nan)
            if "cogs" in s.columns:
                cogs_month = s.groupby("period", as_index=False).agg(
                    cogs=("cogs", lambda x: x.sum(min_count=1)),
                    cogs_rows=("cogs", "count"),
                )
                monthly = monthly.merge(cogs_month, on="period", how="left")
                monthly["cogs_coverage_pct"] = np.where(monthly["sales_rows"] > 0, monthly["cogs_rows"] / monthly["sales_rows"] * 100, np.nan)
                monthly["gross_profit"] = monthly["revenue"] - monthly["cogs"]
                monthly["gross_margin_pct"] = np.where(monthly["revenue"] != 0, monthly["gross_profit"] / monthly["revenue"] * 100, np.nan)
    if not expenses.empty and "amount" in expenses.columns:
        expense_sum = _num(expenses, "amount").sum(min_count=1)
        kpis["expenses_total"] = _money(expense_sum)
        if "transaction_date" in expenses.columns:
            e = expenses.dropna(subset=["transaction_date"]).copy()
            e["period"] = pd.to_datetime(e["transaction_date"]).dt.to_period("M").astype(str)
            exp_month = e.groupby("period", as_index=False)["amount"].sum(min_count=1).rename(columns={"amount": "expenses"})
            monthly = monthly.merge(exp_month, on="period", how="outer") if not monthly.empty else exp_month
    if "gross_profit_total" in kpis and "expenses_total" in kpis:
        kpis["gross_profit_less_supplied_expenses"] = _money(kpis["gross_profit_total"] - kpis["expenses_total"])
        kpis["operating_result_note"] = "Gross profit less supplied expense records only; not a complete operating profit unless all operating costs and accounting adjustments are included."
    return {"kpis": kpis, "monthly_performance": _records(monthly.sort_values("period") if "period" in monthly.columns else monthly), "available": True}


def calculate_sales_intelligence(tables: dict[str, pd.DataFrame]) -> dict:
    sales = tables.get("sales", pd.DataFrame()).copy()
    if sales.empty or "revenue" not in sales.columns:
        return {}
    sales["revenue"] = _num(sales, "revenue")
    result: dict[str, Any] = {"total_revenue": _money(sales["revenue"].sum(min_count=1)), "transaction_lines": int(len(sales))}
    if "invoice_id" in sales.columns:
        result["invoice_count"] = int(sales["invoice_id"].nunique(dropna=True))
        result["average_invoice_value"] = _money(sales.groupby("invoice_id")["revenue"].sum().mean())
    for field, label in [("product_name", "by_product"), ("product_id", "by_product_id"), ("customer_name", "by_customer"), ("customer_id", "by_customer_id"), ("category", "by_category"), ("salesperson", "by_salesperson"), ("sales_channel", "by_channel")]:
        if field in sales.columns:
            grouped = sales.groupby(field, dropna=False)["revenue"].sum().sort_values(ascending=False).head(20).reset_index()
            result[label] = _records(grouped.rename(columns={field: "dimension", "revenue": "revenue"}))
    if "customer_id" in sales.columns:
        cust = sales.groupby("customer_id")["revenue"].sum().sort_values(ascending=False)
        total = cust.sum()
        result["top_5_customer_revenue_share_pct"] = round(float(cust.head(5).sum() / total * 100), 2) if total else None
    if "transaction_date" in sales.columns:
        s = sales.dropna(subset=["transaction_date"]).copy()
        s["period"] = pd.to_datetime(s["transaction_date"]).dt.to_period("M").astype(str)
        result["monthly_sales"] = _records(s.groupby("period", as_index=False)["revenue"].sum().sort_values("period"))
    return result


def calculate_cost_intelligence(tables: dict[str, pd.DataFrame]) -> dict:
    expenses = tables.get("expenses", pd.DataFrame()).copy()
    if expenses.empty or "amount" not in expenses.columns:
        return {}
    expenses["amount"] = _num(expenses, "amount")
    result = {"total_expenses": _money(expenses["amount"].sum(min_count=1)), "expense_records": int(len(expenses))}
    for field, label in [("category", "by_category"), ("department", "by_department"), ("store_id", "by_store")]:
        if field in expenses.columns:
            result[label] = _records(expenses.groupby(field, dropna=False, as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(30))
    if "transaction_date" in expenses.columns:
        e = expenses.dropna(subset=["transaction_date"]).copy()
        e["period"] = pd.to_datetime(e["transaction_date"]).dt.to_period("M").astype(str)
        result["monthly_expenses"] = _records(e.groupby("period", as_index=False)["amount"].sum().sort_values("period"))
    return result


def calculate_inventory(tables: dict[str, pd.DataFrame], snapshot: pd.Timestamp) -> dict:
    inv = derive_inventory_snapshot(tables, snapshot)
    if inv.empty or "closing_quantity" not in inv.columns:
        return {}
    inv["closing_quantity"] = _num(inv, "closing_quantity")
    if "reorder_level" in inv.columns:
        inv["reorder_level"] = _num(inv, "reorder_level")
        inv["below_reorder"] = (inv["closing_quantity"] >= 0) & (inv["closing_quantity"] < inv["reorder_level"])
    if "inventory_value" not in inv.columns and "unit_cost" in inv.columns:
        inv["inventory_value"] = inv["closing_quantity"] * _num(inv, "unit_cost")
    if "days_since_last_sale" not in inv.columns and "last_sale_date" in inv.columns:
        inv["days_since_last_sale"] = (snapshot - pd.to_datetime(inv["last_sale_date"], errors="coerce")).dt.days
    result = {"stock_items": int(inv["product_id"].nunique(dropna=True)) if "product_id" in inv.columns else int(len(inv)), "closing_units": _money(inv["closing_quantity"].sum(min_count=1))}
    if "inventory_value" in inv.columns:
        result["indicative_inventory_value"] = _money(_num(inv, "inventory_value").sum(min_count=1))
    inv["negative_stock"] = inv["closing_quantity"] < 0
    result["items_negative_stock"] = int(inv["negative_stock"].sum())
    if "inventory_value" in inv.columns:
        result["negative_stock_value"] = _money(_num(inv.loc[inv["negative_stock"]], "inventory_value").sum(min_count=1))
    if "below_reorder" in inv.columns:
        result["items_below_reorder"] = int(inv["below_reorder"].sum())
    if "days_since_last_sale" in inv.columns:
        result["items_no_sale_90_days"] = int((_num(inv, "days_since_last_sale") >= 90).sum())
    result["product_detail"] = _records(inv.sort_values("closing_quantity", ascending=True).head(100))
    return result


def calculate_ageing(df: pd.DataFrame, as_of: pd.Timestamp, party_field: str) -> dict:
    if df.empty or "outstanding_amount" not in df.columns or "due_date" not in df.columns:
        return {}
    work = df.copy()
    work["outstanding_amount"] = _num(work, "outstanding_amount")
    work["due_date"] = pd.to_datetime(work["due_date"], errors="coerce")
    work = work[work["outstanding_amount"].notna() & (work["outstanding_amount"] > 0)].copy()
    work["days_overdue"] = (as_of - work["due_date"]).dt.days
    work["age_bucket"] = np.select(
        [work["due_date"].isna(), work["days_overdue"] <= 0, work["days_overdue"] <= 30, work["days_overdue"] <= 60, work["days_overdue"] <= 90],
        ["Unknown due date", "Not due", "1-30 days", "31-60 days", "61-90 days"], default="90+ days"
    )
    ageing = work.groupby("age_bucket", as_index=False)["outstanding_amount"].sum()
    overdue = work[work["days_overdue"] > 0]
    total = work["outstanding_amount"].sum()
    result = {"outstanding_total": _money(total), "overdue_total": _money(overdue["outstanding_amount"].sum()), "overdue_share_pct": round(float(overdue["outstanding_amount"].sum() / total * 100), 2) if total else None, "ageing_buckets": _records(ageing), "overdue_documents": int(len(overdue))}
    if party_field in work.columns:
        result["largest_parties"] = _records(work.groupby(party_field, as_index=False)["outstanding_amount"].sum().sort_values("outstanding_amount", ascending=False).head(20))
    return result


def calculate_procurement(tables: dict[str, pd.DataFrame]) -> dict:
    p = tables.get("purchases", pd.DataFrame()).copy()
    if p.empty:
        return {}
    result = {"purchase_records": int(len(p))}
    if "purchase_value" not in p.columns and {"quantity", "unit_cost"}.issubset(p.columns):
        p["purchase_value"] = _num(p, "quantity") * _num(p, "unit_cost")
    if "purchase_value" in p.columns:
        result["purchase_value_total"] = _money(_num(p, "purchase_value").sum(min_count=1))
    for field, label in [("supplier_name", "by_supplier"), ("supplier_id", "by_supplier_id"), ("product_name", "by_product")]:
        if field in p.columns and "purchase_value" in p.columns:
            result[label] = _records(p.groupby(field, dropna=False, as_index=False)["purchase_value"].sum().sort_values("purchase_value", ascending=False).head(30))
    if {"transaction_date", "unit_cost"}.issubset(p.columns):
        p["period"] = pd.to_datetime(p["transaction_date"], errors="coerce").dt.to_period("M").astype(str)
        p["unit_cost"] = _num(p, "unit_cost")
        keys = [c for c in ["product_id", "supplier_id", "period"] if c in p.columns]
        if keys:
            qty = _num(p, "quantity") if "quantity" in p.columns else None
            if qty is not None and qty.notna().any():
                # Quantity-weighted average cost (sum(cost*qty)/sum(qty)); a simple mean of line costs mis-weights small and large lines.
                p["_w_cost"] = p["unit_cost"] * qty
                p["_w_qty"] = qty.where(p["unit_cost"].notna())
                g = p.groupby(keys, dropna=False, as_index=False).agg(_w_cost=("_w_cost", "sum"), _w_qty=("_w_qty", "sum"))
                g["unit_cost"] = np.where(g["_w_qty"] > 0, g["_w_cost"] / g["_w_qty"], np.nan)
                trends = g.drop(columns=["_w_cost", "_w_qty"])
            else:
                trends = p.groupby(keys, dropna=False, as_index=False)["unit_cost"].mean()
            result["unit_cost_trends"] = _records(trends.sort_values("period" if "period" in keys else keys[0]))
            if "product_id" in keys and "period" in keys:
                # Product-level monthly cost across suppliers, quantity-weighted when quantity exists; used for price-change findings.
                pk = ["product_id", "period"]
                if qty is not None and qty.notna().any():
                    gp_ = p.groupby(pk, dropna=False, as_index=False).agg(_w_cost=("_w_cost", "sum"), _w_qty=("_w_qty", "sum"))
                    gp_["unit_cost"] = np.where(gp_["_w_qty"] > 0, gp_["_w_cost"] / gp_["_w_qty"], np.nan)
                    gp_ = gp_.drop(columns=["_w_cost", "_w_qty"])
                else:
                    gp_ = p.groupby(pk, dropna=False, as_index=False)["unit_cost"].mean()
                result["unit_cost_trends_by_product"] = _records(gp_.sort_values(pk))
    return result


def calculate_retail_store(tables: dict[str, pd.DataFrame]) -> dict:
    s = tables.get("sales", pd.DataFrame()).copy()
    if s.empty or "store_id" not in s.columns or "revenue" not in s.columns:
        return {}
    s["revenue"] = _num(s, "revenue")
    aggregations = {"revenue": ("revenue", "sum")}
    if "invoice_id" in s.columns:
        aggregations["invoice_count"] = ("invoice_id", "nunique")
    if "quantity" in s.columns:
        aggregations["units_sold"] = ("quantity", "sum")
    grouped = s.groupby("store_id", dropna=False).agg(**aggregations).reset_index()
    if "invoice_count" in grouped.columns:
        grouped["average_basket_value"] = grouped["revenue"] / grouped["invoice_count"].replace(0, np.nan)
    return {"store_count": int(s["store_id"].nunique(dropna=True)), "store_performance": _records(grouped.sort_values("revenue", ascending=False))}


def calculate_service_projects(tables: dict[str, pd.DataFrame]) -> dict:
    projects = tables.get("service_projects", pd.DataFrame()).copy()
    timesheets = tables.get("timesheets", pd.DataFrame()).copy()
    result = {}
    if not projects.empty:
        if {"project_revenue", "project_cost"}.issubset(projects.columns):
            projects["project_revenue"] = _num(projects, "project_revenue")
            projects["project_cost"] = _num(projects, "project_cost")
            valid = projects["project_revenue"].notna() & projects["project_cost"].notna()
            projects["project_margin"] = projects["project_revenue"] - projects["project_cost"]
            projects["project_margin_pct"] = np.where(projects["project_revenue"] != 0, projects["project_margin"] / projects["project_revenue"] * 100, np.nan)
            result["project_revenue_total"] = _money(projects["project_revenue"].sum(min_count=1))
            result["project_cost_total"] = _money(projects["project_cost"].sum(min_count=1))
            result["project_margin_total"] = _money(projects.loc[valid, "project_margin"].sum())
            result["projects_with_complete_margin_data"] = int(valid.sum())
        result["projects"] = _records(projects.head(100))
    if not timesheets.empty:
        result["hours_total"] = _money(_num(timesheets, "hours").sum(min_count=1)) if "hours" in timesheets else None
        if "billable_hours" in timesheets and "hours" in timesheets:
            hours = _num(timesheets, "hours").sum()
            billable = _num(timesheets, "billable_hours").sum()
            result["billable_utilisation_pct"] = round(float(billable / hours * 100), 2) if hours else None
        result["timesheet_rows"] = int(len(timesheets))
    return result



def calculate_product_profitability(tables: dict[str, pd.DataFrame]) -> dict:
    sales = tables.get("sales", pd.DataFrame()).copy()
    if sales.empty or not {"product_id", "revenue", "cogs"}.issubset(sales.columns):
        return {}
    sales["revenue"] = _num(sales, "revenue")
    sales["cogs"] = _num(sales, "cogs")
    valid = sales["revenue"].notna() & sales["cogs"].notna()
    work = sales.loc[valid].copy()
    if work.empty:
        return {"cost_data_coverage_pct": 0.0, "by_product": []}
    work["gross_profit"] = work["revenue"] - work["cogs"]
    group_cols = ["product_id"] + (["product_name"] if "product_name" in work.columns else [])
    grouped = work.groupby(group_cols, dropna=False, as_index=False).agg(revenue=("revenue", "sum"), cogs=("cogs", "sum"), gross_profit=("gross_profit", "sum"))
    grouped["gross_margin_pct"] = np.where(grouped["revenue"] != 0, grouped["gross_profit"] / grouped["revenue"] * 100, np.nan)
    result = {"cost_data_coverage_pct": round(float(valid.mean() * 100), 2), "by_product": _records(grouped.sort_values("gross_profit", ascending=False).head(100))}
    if "customer_id" in work.columns:
        customer_cols = ["customer_id"] + (["customer_name"] if "customer_name" in work.columns else [])
        by_customer = work.groupby(customer_cols, dropna=False, as_index=False).agg(revenue=("revenue", "sum"), cogs=("cogs", "sum"))
        by_customer["gross_profit"] = by_customer["revenue"] - by_customer["cogs"]
        by_customer["gross_margin_pct"] = np.where(by_customer["revenue"] != 0, by_customer["gross_profit"] / by_customer["revenue"] * 100, np.nan)
        result["by_customer"] = _records(by_customer.sort_values("gross_profit", ascending=False).head(100))
    if "category" in work.columns:
        by_category = work.groupby("category", dropna=False, as_index=False).agg(revenue=("revenue", "sum"), cogs=("cogs", "sum"))
        by_category["gross_profit"] = by_category["revenue"] - by_category["cogs"]
        by_category["gross_margin_pct"] = np.where(by_category["revenue"] != 0, by_category["gross_profit"] / by_category["revenue"] * 100, np.nan)
        result["by_category"] = _records(by_category.sort_values("gross_profit", ascending=False).head(100))
    return result


def calculate_working_capital(tables: dict[str, pd.DataFrame], inventory_result: dict, ar_result: dict, ap_result: dict) -> dict:
    inventory_value = inventory_result.get("indicative_inventory_value") if inventory_result else None
    ar_value = ar_result.get("outstanding_total") if ar_result else None
    ap_value = ap_result.get("outstanding_total") if ap_result else None
    available = {"receivables": ar_value is not None, "inventory": inventory_value is not None, "payables": ap_value is not None}
    result = {"balances": {"receivables": ar_value, "inventory": inventory_value, "payables": ap_value}, "available_components": available}
    if ar_value is not None and inventory_value is not None:
        result["trade_working_capital_before_payables"] = _money(ar_value + inventory_value)
    if ar_value is not None and inventory_value is not None and ap_value is not None:
        result["net_trade_working_capital"] = _money(ar_value + inventory_value - ap_value)
    else:
        result["net_trade_working_capital"] = None
        result["limitation"] = "Net trade working capital is not calculated until receivables, inventory and payables balances are all available on a comparable date and basis."
    return result if any(available.values()) else {}


def calculate_collections(tables: dict[str, pd.DataFrame]) -> dict:
    payments = tables.get("payments", pd.DataFrame()).copy()
    if payments.empty or not {"transaction_date", "amount"}.issubset(payments.columns):
        return {}
    payments["amount"] = _num(payments, "amount")
    result = {"payment_total": _money(payments["amount"].sum(min_count=1)), "payment_records": int(len(payments))}
    p = payments.dropna(subset=["transaction_date"]).copy()
    p["period"] = pd.to_datetime(p["transaction_date"]).dt.to_period("M").astype(str)
    result["monthly_collections"] = _records(p.groupby("period", as_index=False)["amount"].sum().sort_values("period"))
    party_field = "party_id" if "party_id" in p.columns else ("party_name" if "party_name" in p.columns else None)
    if party_field:
        result["collections_by_party"] = _records(p.groupby(party_field, dropna=False, as_index=False)["amount"].sum().sort_values("amount", ascending=False).head(30))
    return result


def calculate_reconciliations(tables: dict[str, pd.DataFrame]) -> dict:
    checks = []
    detail_tables: dict[str, list[dict]] = {}
    sales = tables.get("sales", pd.DataFrame()).copy()
    ar = tables.get("receivables", pd.DataFrame()).copy()
    if not sales.empty and not ar.empty and {"invoice_id", "revenue"}.issubset(sales.columns) and {"invoice_id", "invoice_amount"}.issubset(ar.columns):
        sales_basis = sales.copy()
        if "tax_amount" in sales_basis.columns and sales_basis["tax_amount"].notna().any():
            # Receivable invoices carry tax (GST/VAT); compare like-for-like by adding the supplied tax to net revenue.
            sales_basis["revenue"] = _num(sales_basis, "revenue") + _num(sales_basis, "tax_amount").fillna(0)
        left = sales_basis.dropna(subset=["invoice_id"]).groupby("invoice_id", as_index=False)["revenue"].sum(min_count=1).rename(columns={"revenue": "sales_revenue"})
        right = ar.dropna(subset=["invoice_id"]).groupby("invoice_id", as_index=False)["invoice_amount"].sum(min_count=1)
        joined = left.merge(right, on="invoice_id", how="inner")
        if not joined.empty:
            joined["variance"] = _num(joined, "sales_revenue") - _num(joined, "invoice_amount")
            joined["variance_abs"] = joined["variance"].abs()
            mismatch = joined[joined["variance_abs"] > 0.05]
            checks.append({"check": "sales_vs_receivables_invoice_amount", "matched_invoices": int(len(joined)), "mismatched_invoices": int(len(mismatch)), "absolute_variance_total": _money(mismatch["variance_abs"].sum()), "status": "review" if len(mismatch) else "passed", "tolerance": 0.05})
            detail_tables["sales_vs_receivables"] = _records(joined.sort_values("variance_abs", ascending=False).head(100))
        payments = tables.get("payments", pd.DataFrame()).copy()
        if not payments.empty and {"invoice_id", "amount"}.issubset(payments.columns) and "paid_amount" in ar.columns:
            paid = payments.dropna(subset=["invoice_id"]).groupby("invoice_id", as_index=False)["amount"].sum(min_count=1).rename(columns={"amount": "payment_register_total"})
            ar_paid = ar.dropna(subset=["invoice_id"]).groupby("invoice_id", as_index=False)["paid_amount"].sum(min_count=1)
            pjoin = ar_paid.merge(paid, on="invoice_id", how="inner")
            if not pjoin.empty:
                pjoin["variance"] = _num(pjoin, "paid_amount") - _num(pjoin, "payment_register_total")
                pjoin["variance_abs"] = pjoin["variance"].abs()
                pmismatch = pjoin[pjoin["variance_abs"] > 0.05]
                checks.append({"check": "receivables_paid_vs_payment_register", "matched_invoices": int(len(pjoin)), "mismatched_invoices": int(len(pmismatch)), "absolute_variance_total": _money(pmismatch["variance_abs"].sum()), "status": "review" if len(pmismatch) else "passed", "tolerance": 0.05})
                detail_tables["paid_vs_payment_register"] = _records(pjoin.sort_values("variance_abs", ascending=False).head(100))
    inv = tables.get("inventory_snapshot", pd.DataFrame()).copy()
    movements = tables.get("inventory_movements", pd.DataFrame()).copy()
    if not inv.empty and not movements.empty and {"product_id", "closing_quantity"}.issubset(inv.columns) and {"product_id", "quantity_delta"}.issubset(movements.columns):
        closing = inv.dropna(subset=["product_id"]).groupby("product_id", as_index=False)["closing_quantity"].sum(min_count=1)
        ledger = movements.dropna(subset=["product_id"]).groupby("product_id", as_index=False)["quantity_delta"].sum(min_count=1).rename(columns={"quantity_delta": "movement_net_quantity"})
        join = closing.merge(ledger, on="product_id", how="inner")
        if not join.empty:
            join["variance"] = _num(join, "closing_quantity") - _num(join, "movement_net_quantity")
            join["variance_abs"] = join["variance"].abs()
            mismatch = join[join["variance_abs"] > 0.0001]
            checks.append({"check": "inventory_snapshot_vs_movement_ledger", "matched_products": int(len(join)), "mismatched_products": int(len(mismatch)), "absolute_variance_total_units": _money(mismatch["variance_abs"].sum()), "status": "review" if len(mismatch) else "passed", "tolerance_units": 0.0001})
            detail_tables["inventory_reconciliation"] = _records(join.sort_values("variance_abs", ascending=False).head(100))
    if not sales.empty and {"revenue", "cogs", "gross_profit"}.issubset(sales.columns):
        valid = sales[["revenue", "cogs", "gross_profit"]].notna().all(axis=1)
        if valid.any():
            check = sales.loc[valid, ["revenue", "cogs", "gross_profit"]].copy()
            check["calculated_gross_profit"] = _num(check, "revenue") - _num(check, "cogs")
            check["variance"] = _num(check, "gross_profit") - check["calculated_gross_profit"]
            check["variance_abs"] = check["variance"].abs()
            mismatch = check[check["variance_abs"] > 0.015]
            checks.append({"check": "source_gross_profit_vs_recalculated", "matched_rows": int(len(check) - len(mismatch)), "mismatched_rows": int(len(mismatch)), "absolute_variance_total": _money(mismatch["variance_abs"].sum()), "status": "review" if len(mismatch) else "passed", "tolerance": 0.015})
            detail_tables["gross_profit_reconciliation"] = _records(check.sort_values("variance_abs", ascending=False).head(100))
    if not inv.empty and {"product_id", "closing_quantity"}.issubset(inv.columns):
        neg = inv.assign(closing_quantity=_num(inv, "closing_quantity"))
        neg = neg[neg["closing_quantity"] < 0]
        checks.append({"check": "inventory_no_negative_closing_stock", "checked_products": int(inv["product_id"].nunique()), "negative_stock_products": int(neg["product_id"].nunique()), "status": "review" if len(neg) else "passed"})
        if len(neg):
            detail_tables["negative_stock"] = _records(neg[[c for c in ["product_id", "product_name", "closing_quantity"] if c in neg.columns]].sort_values("closing_quantity").head(100))
    if not checks:
        return {}
    return {"checks": checks, "check_count": len(checks), "checks_requiring_review": sum(1 for c in checks if c["status"] == "review"), "details": detail_tables}

def module_availability(tables: dict[str, pd.DataFrame], profile: str) -> list[dict]:
    results = []
    for module, meta in MODULES.items():
        available = True
        reasons = []
        for dataset, fields in meta["requires"].items():
            frame = tables.get(dataset, pd.DataFrame())
            if frame.empty:
                available = False
                reasons.append(f"{dataset} data not supplied")
                continue
            for field in fields:
                if field not in frame.columns or frame[field].isna().all():
                    available = False
                    reasons.append(f"{dataset}.{field} unavailable")
        results.append({"module": module, "label": meta["label"], "available": available, "profile_relevance": profile, "reason": "Available" if available else "; ".join(reasons)})
    return results


def build_insights(tables: dict[str, pd.DataFrame], module_results: dict, as_of: pd.Timestamp, thresholds: dict | None = None) -> list[dict]:
    thresholds = thresholds or {}
    insights: list[dict] = []
    def add(code, severity, title, finding, evidence, recommendation, limitation=""):
        insights.append({"insight_id": code, "severity": severity, "title": title, "finding": finding, "evidence": evidence, "recommended_action": recommendation, "limitation": limitation})

    monthly = pd.DataFrame(module_results.get("financial_performance", {}).get("monthly_performance", []))
    rev_drop = float(thresholds.get("revenue_decline_pct", 10))
    margin_drop = float(thresholds.get("margin_decline_pp", 2))
    expense_rise = float(thresholds.get("expense_increase_pct", 15))
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        revenue_coverage_ok = min(float(last.get("revenue_coverage_pct", 0) or 0), float(prev.get("revenue_coverage_pct", 0) or 0)) >= 95
        if revenue_coverage_ok and pd.notna(prev.get("revenue")) and prev.get("revenue") != 0:
            change = (float(last.get("revenue", 0)) / float(prev["revenue"]) - 1) * 100
            if change <= -rev_drop:
                add("REV_TREND_001", "high", "Revenue declined materially", f"Revenue decreased {abs(change):.1f}% versus the previous available month.", {"current_period": last.get("period"), "previous_period": prev.get("period"), "current_revenue": _money(last.get("revenue")), "previous_revenue": _money(prev.get("revenue")), "change_pct": round(change, 2)}, "Review product, customer and location-level changes; separate volume, price and mix effects before taking action.", "Monthly comparison is based only on uploaded sales records and may not account for cut-off or missing transactions.")
        cogs_coverage_ok = min(float(last.get("cogs_coverage_pct", 0) or 0), float(prev.get("cogs_coverage_pct", 0) or 0)) >= 95
        if cogs_coverage_ok and "gross_margin_pct" in monthly and pd.notna(prev.get("gross_margin_pct")) and pd.notna(last.get("gross_margin_pct")):
            delta = float(last["gross_margin_pct"]) - float(prev["gross_margin_pct"])
            if delta <= -margin_drop:
                add("MARGIN_TREND_001", "high", "Gross margin compressed", f"Gross margin declined by {abs(delta):.1f} percentage points.", {"current_period": last.get("period"), "current_margin_pct": round(float(last["gross_margin_pct"]), 2), "previous_margin_pct": round(float(prev["gross_margin_pct"]), 2), "change_pp": round(delta, 2)}, "Review purchase costs, selling prices, discounts and product/customer mix for the affected period.", "Requires complete revenue and cost-of-goods data for comparable periods.")
    cost_months = pd.DataFrame(module_results.get("cost_intelligence", {}).get("monthly_expenses", []))
    if len(cost_months) >= 2:
        last, prev = cost_months.iloc[-1], cost_months.iloc[-2]
        if pd.notna(prev.get("amount")) and prev.get("amount") > 0:
            change = (float(last.get("amount", 0)) / float(prev["amount"]) - 1) * 100
            if change >= expense_rise:
                add("COST_TREND_001", "medium", "Expenses increased materially", f"Supplied expenses increased {change:.1f}% versus the previous available month.", {"current_period": last.get("period"), "current_expenses": _money(last.get("amount")), "previous_expenses": _money(prev.get("amount")), "change_pct": round(change, 2)}, "Review category-level movements and validate whether the increase is recurring, seasonal or one-off.", "Expense completeness and accounting cut-off have not been independently verified.")
    ar = module_results.get("receivables_intelligence", {})
    overdue_share = ar.get("overdue_share_pct")
    rec = tables.get("receivables", pd.DataFrame())
    if not rec.empty and {"customer_id", "due_date", "outstanding_amount"}.issubset(rec.columns):
        r_ = rec.copy(); r_["outstanding_amount"] = _num(r_, "outstanding_amount")
        od = r_[(pd.to_datetime(r_["due_date"], errors="coerce") < as_of) & (r_["outstanding_amount"] > 0)].copy()
        if not od.empty and od["outstanding_amount"].sum() > 0:
            od["days_overdue"] = (as_of - pd.to_datetime(od["due_date"])).dt.days
            by = od.groupby("customer_id").agg(overdue=("outstanding_amount", "sum"), oldest_days=("days_overdue", "max"), invoices=("outstanding_amount", "size")).sort_values("overdue", ascending=False)
            total_od = float(by["overdue"].sum()); top_id = by.index[0]; top = by.iloc[0]; share = top["overdue"] / total_od * 100
            names = tables.get("customers", pd.DataFrame())
            label = top_id
            if not names.empty and {"customer_id", "customer_name"}.issubset(names.columns):
                hit = names.loc[names["customer_id"] == top_id, "customer_name"]
                label = f"{hit.iloc[0]} ({top_id})" if len(hit) else top_id
            if share >= float(thresholds.get("customer_overdue_share_pct", 15)) and top["oldest_days"] > 60:
                add("AR_CUST_001", "high", "Single customer holds a large share of overdue receivables", f"{label} accounts for {share:.1f}% of overdue receivables ({_money(top['overdue']):,.2f} across {int(top['invoices'])} invoices, oldest {int(top['oldest_days'])} days overdue).", {"customer_id": top_id, "customer_overdue": _money(top["overdue"]), "share_of_overdue_pct": round(float(share), 2), "oldest_days_overdue": int(top["oldest_days"]), "total_overdue": _money(total_od)}, "Review the account with the client: confirm disputes, stop-supply or credit-limit action, and whether a provision or follow-up plan is needed.", "Based on supplied due dates and balances only; does not know about agreed payment plans or disputes.")
    if overdue_share is not None and overdue_share >= float(thresholds.get("overdue_share_pct", 30)):
        add("AR_AGE_001", "high", "Overdue receivables concentration", f"{overdue_share:.1f}% of supplied outstanding receivables are overdue as of {as_of.date()}.", {"outstanding_total": ar.get("outstanding_total"), "overdue_total": ar.get("overdue_total"), "overdue_share_pct": overdue_share}, "Prioritise collection review by overdue amount, days past due, customer credit exposure and dispute status.", "Ageing is calculated from due dates and outstanding amounts supplied by the client.")
    inv = module_results.get("inventory_intelligence", {})
    low = inv.get("items_below_reorder")
    if low is not None and low > 0:
        add("INV_LOW_001", "medium", "Items below configured reorder level", f"{low} products are below their supplied reorder level.", {"items_below_reorder": low}, "Review demand, supplier lead times, open purchase orders and service levels before replenishing.", "Reorder recommendations are not calculated without validated lead times, open orders and demand assumptions.")
    neg_items = inv.get("items_negative_stock")
    if neg_items:
        add("INV_NEG_001", "high", "Negative closing stock recorded", f"{neg_items} products show negative closing stock, which is not physically possible.", {"items_negative_stock": neg_items, "negative_stock_value": inv.get("negative_stock_value")}, "Check for unrecorded receipts, sales posted against the wrong product, missing opening balances or cut-off errors before relying on stock value or reorder decisions.", "Indicative stock value nets negative items against positive ones and is therefore understated until these are corrected.")
    fp = module_results.get("financial_performance", {}).get("kpis", {})
    gp, opex = fp.get("gross_profit_total"), fp.get("expenses_total")
    if gp is not None and opex is not None and gp > 0 and opex > gp and float(fp.get("gross_profit_data_coverage_pct", 0) or 0) >= 95:
        add("OPEX_COVER_001", "high", "Supplied expenses exceed gross profit", f"Supplied expenses ({opex:,.2f}) are {opex / gp:.1f}x gross profit ({gp:,.2f}) for the period.", {"gross_profit_total": gp, "expenses_total": opex, "gross_profit_less_supplied_expenses": fp.get("gross_profit_less_supplied_expenses")}, "Confirm the expense ledger covers the same entity and period as sales, excludes capital items and inter-company transfers, and that sales are complete before drawing conclusions.", "Compares supplied records only; may reflect incomplete sales data, mismatched periods or non-operating items rather than a true operating loss.")
    slow = inv.get("items_no_sale_90_days")
    if slow is not None and slow > 0:
        add("INV_SLOW_001", "medium", "Products with no recorded sale for 90+ days", f"{slow} products have no recorded sale for at least 90 days.", {"items_no_sale_90_days": slow}, "Review stock ageing, seasonality, product lifecycle, returns and alternate sales channels before markdown or disposal.", "This check uses supplied last-sale dates or derived sales movements; incomplete sales history can overstate ageing.")
    sales = module_results.get("sales_intelligence", {})
    concentration = sales.get("top_5_customer_revenue_share_pct")
    if concentration is not None and concentration >= float(thresholds.get("top5_customer_share_pct", 50)):
        add("CUST_CONC_001", "medium", "Customer revenue concentration", f"The top five customers account for {concentration:.1f}% of supplied revenue.", {"top_5_customer_revenue_share_pct": concentration}, "Review exposure, credit terms, retention plans and diversification options.", "Customer concentration is calculated only where stable customer IDs are supplied.")
    procurement = module_results.get("procurement_intelligence", {})
    trends = pd.DataFrame(procurement.get("unit_cost_trends_by_product", []))
    if len(trends) and {"period", "unit_cost", "product_id"}.issubset(trends.columns):
        for product, group in trends.dropna(subset=["period", "unit_cost"]).groupby("product_id"):
            group = group.sort_values("period")
            if len(group) >= 2 and float(group.iloc[-2]["unit_cost"]) > 0:
                try:
                    gap = (pd.Period(group.iloc[-1]["period"], "M") - pd.Period(group.iloc[-2]["period"], "M")).n
                except Exception:
                    gap = 1
                if gap != 1:
                    continue  # only compare consecutive months; a gap would not be like-for-like
                change = (float(group.iloc[-1]["unit_cost"]) / float(group.iloc[-2]["unit_cost"]) - 1) * 100
                if change >= float(thresholds.get("supplier_price_increase_pct", 8)):
                    add("PROC_PRICE_001", "medium", "Purchase unit cost increased", f"Average purchase unit cost for product {product} increased {change:.1f}% in the latest compared month.", {"product_id": str(product), "latest_period": group.iloc[-1]["period"], "previous_unit_cost": _money(group.iloc[-2]["unit_cost"]), "latest_unit_cost": _money(group.iloc[-1]["unit_cost"]), "change_pct": round(change, 2)}, "Validate like-for-like unit, supplier, currency, quantity breaks and product specifications before renegotiating.", "Like-for-like comparison depends on consistent product IDs and comparable purchase units.")
    return insights

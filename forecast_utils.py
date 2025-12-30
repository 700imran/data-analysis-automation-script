"""
Forecast utilities upgraded with real-time industry benchmarking via yfinance.
"""

import pandas as pd
import numpy as np
import yfinance as yf

from cashflow_utils import compute_cash_flows
from balance_sheet_utils import (
    compute_working_capital_accounts,
    compute_balance_sheet,
    compute_shareholding_pattern
)
from output_utils import save_output

# ----------------------------
# Benchmarking with yfinance
# ----------------------------

def fetch_benchmark_metrics(benchmark_ticker: str, lookback_years: int = 5) -> dict:
    if not benchmark_ticker:
        return {}

    tkr = yf.Ticker(benchmark_ticker)
    hist = tkr.history(period=f"{lookback_years}y")
    price_growth_pct = 0.08
    if not hist.empty:
        start_p = hist["Close"].iloc[0]
        end_p = hist["Close"].iloc[-1]
        if start_p > 0:
            years = max(1, lookback_years)
            cagr = (end_p / start_p) ** (1 / years) - 1
            price_growth_pct = float(cagr)

    fin = {}
    try:
        fin["financials"] = tkr.financials
        fin["balance_sheet"] = tkr.balance_sheet
        fin["cashflow"] = tkr.cashflow
    except Exception:
        pass

    bench = {
        "revenue_growth_pct": price_growth_pct,
        "cogs_pct_revenue": 0.55,
        "opex_pct_revenue": 0.25,
        "depreciation_pct_revenue": 0.04,
        "capex_pct_revenue": 0.05,
        "tax_rate": 0.25,
        "interest_rate": 0.08,
        "leverage_proxy": 0.15,
    }

    try:
        fin_is = fin.get("financials")
        if isinstance(fin_is, pd.DataFrame) and not fin_is.empty:
            rev_series = fin_is.loc[fin_is.index.str.contains("Total Revenue", case=False, regex=True)].sum()
            cogs_series = fin_is.loc[fin_is.index.str.contains("Cost Of Revenue|Cost of Goods", case=False, regex=True)].sum()
            opex_series = fin_is.loc[fin_is.index.str.contains("Operating Expense|Selling General Administrative", case=False, regex=True)].sum()
            dep_series = fin_is.loc[fin_is.index.str.contains("Depreciation", case=False, regex=True)].sum()

            rev = float(rev_series.max()) if not rev_series.empty else None
            cogs = float(cogs_series.max()) if not cogs_series.empty else None
            opex = float(opex_series.max()) if not opex_series.empty else None
            dep = float(dep_series.max()) if not dep_series.empty else None

            if rev and rev > 0:
                if cogs is not None:
                    bench["cogs_pct_revenue"] = min(0.85, max(0.30, cogs / rev))
                if opex is not None:
                    bench["opex_pct_revenue"] = min(0.50, max(0.10, opex / rev))
                if dep is not None:
                    bench["depreciation_pct_revenue"] = min(0.10, max(0.01, dep / rev))
    except Exception:
        pass

    return bench


def merge_assumptions(live: dict, overrides: dict) -> dict:
    live = live or {}
    overrides = overrides or {}
    return {**live, **overrides}

# ----------------------------
# Income statement
# ----------------------------

def build_income_statement(assumptions: dict) -> pd.DataFrame:
    start_year = assumptions.get("start_year", 2025)
    term = assumptions.get("term_years", 5)
    years = list(range(start_year, start_year + term))

    revenue, cogs, opex, depreciation, ebit, interest, ebt, taxes, net_income = ([] for _ in range(9))

    rev = assumptions.get("revenue_start", 10_000_000.0)
    growth = assumptions.get("revenue_growth_pct", 0.10)

    for i, yr in enumerate(years):
        if i == 0:
            revenue.append(rev)
        else:
            rev = rev * (1.0 + growth)
            revenue.append(rev)

        cogs_pct = assumptions.get("cogs_pct_revenue", 0.55)
        opex_pct = assumptions.get("opex_pct_revenue", 0.25)
        dep_pct = assumptions.get("depreciation_pct_revenue", 0.04)

        cogs_val = revenue[-1] * cogs_pct
        opex_val = revenue[-1] * opex_pct
        dep_val = revenue[-1] * dep_pct

        cogs.append(cogs_val)
        opex.append(opex_val)
        depreciation.append(dep_val)

        ebit_val = revenue[-1] - cogs_val - opex_val - dep_val
        ebit.append(ebit_val)

        debt_opening = assumptions.get("debt_opening", revenue[0] * assumptions.get("leverage_proxy", 0.15))
        interest_rate = assumptions.get("interest_rate", 0.08)
        interest_val = debt_opening * interest_rate
        interest.append(interest_val)

        ebt_val = ebit_val - interest_val
        ebt.append(ebt_val)

        tax_rate = assumptions.get("tax_rate", 0.25)
        tax_val = max(0.0, ebt_val * tax_rate)
        taxes.append(tax_val)

        net_income.append(ebt_val - tax_val)

    return pd.DataFrame({
        "Year": years,
        "Revenue": revenue,
        "COGS": cogs,
        "Opex": opex,
        "Depreciation": depreciation,
        "EBIT": ebit,
        "Interest": interest,
        "EBT": ebt,
        "Taxes": taxes,
        "NetIncome": net_income
    })

# ----------------------------
# Three-statement builder
# ----------------------------

def build_three_statement_model(assumptions: dict, opening_balances: dict = None, ownership: dict = None) -> dict:
    benchmark_ticker = (assumptions or {}).get("benchmark_ticker")
    live = fetch_benchmark_metrics(benchmark_ticker) if benchmark_ticker else {}
    merged = merge_assumptions(live, assumptions)

    income_df = build_income_statement(merged)
    wc_df = compute_working_capital_accounts(income_df, merged)
    cash_flow_df = compute_cash_flows(income_df, merged, wc_df)
    balance_df = compute_balance_sheet(income_df, cash_flow_df, merged, opening_balances)
    share_df = compute_shareholding_pattern(balance_df, ownership) if ownership else None

    return {
        "income_statement": income_df,
        "cash_flow": cash_flow_df,
        "balance_sheet": balance_df,
        "shareholding": share_df,
        "assumptions_effective": merged
    }

# ----------------------------
# Interactive helpers
# ----------------------------

def get_forecast_assumptions():
    revenue_start = float(input("Enter starting revenue assumption: "))
    term_years = int(input("Enter forecast term (years): "))
    benchmark_ticker = input("Enter industry ticker/benchmark (e.g., WMT, AAPL): ").strip()
    start_year = int(input("Enter starting forecast year (e.g., 2026): "))
    discount_rate = float(input("Enter discount rate (e.g., 0.12): "))

    return {
        "revenue_start": revenue_start,
        "term_years": term_years,
        "benchmark_ticker": benchmark_ticker,
        "start_year": start_year,
        "discount_rate": discount_rate
    }

def get_opening_balances():
    return {
        "cash_opening": 1_000_000,
        "ppne_opening": 3_500_000,
        "debt_opening": 2_000_000,
        "equity_opening": 2_000_000
    }

# ----------------------------
# Valuation helpers
# ----------------------------

def compute_free_cash_flow(cash_flow_df: pd.DataFrame) -> pd.DataFrame:
    out = cash_flow_df.copy()
    out["FCF"] = out["OperatingCF"] + out["InvestingCF"]
    return out[["Year", "FCF"]]

def simple_dcf(fcf_df: pd.DataFrame, assumptions: dict) -> pd.DataFrame:
    dr = assumptions.get("discount_rate", 0.12)
    discounted = []
    for i, row in enumerate(fcf_df.itertuples(index=False)):
        year_index = i + 1
        discounted_val = row.FCF / ((1.0 + dr) ** year_index)
        discounted.append(discounted_val)
    return pd.DataFrame({"Year": fcf_df["Year"], "FCF": fcf_df["FCF"], "DiscountedFCF": discounted})

# ----------------------------
# Standalone forecast wrapper
# ----------------------------

def run_forecast(filepath=None, ownership=None):
    assumptions = get_forecast_assumptions()
    opening_balances = get_opening_balances()

    model = build_three_statement_model(assumptions, opening_balances, ownership)

    income = model["income_statement"]
    cashflow = model["cash_flow"]
    balance = model["balance_sheet"]
    share = model["shareholding"]

    fcf = compute_free_cash_flow(cashflow)
    dcf = simple_dcf(fcf, assumptions)

    # Save outputs
    save_output(income, filepath, "income_statement")
    save_output(cashflow, filepath, "cash_flow_statement")
    save_output(balance, filepath, "balance_sheet")
    if share is not None:
        save_output(share, filepath, "shareholding_pattern")
    save_output(fcf, filepath, "free_cash_flow")
    save_output(dcf, filepath, "discounted_fcf")

    ev = float(dcf["DiscountedFCF"].sum())
    npv = ev

    print("✅ Three-statement model generated and saved.")
    print(f"Enterprise Value: {ev}")
    print(f"Net Present Value: {npv}")

    return {
        "income_statement": income,
        "cash_flow": cashflow,
        "balance_sheet": balance,
        "shareholding": share,
        "fcf": fcf,
        "dcf": dcf,
        "enterprise_value": ev,
        "net_present_value": npv
    }



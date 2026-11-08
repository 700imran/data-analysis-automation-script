# cashflow_utils.py
"""
Cash Flow utilities for three-statement model.

Business role:
- Provide Operating, Investing, and Financing cash flows.
- Link Net Income, Depreciation, Working Capital changes, Capex, Debt, Equity, Dividends.
- Produce Net Change in Cash per year for Balance Sheet linkage.
"""

import pandas as pd

def compute_working_capital_change(wc_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute year-over-year change in Net Working Capital.
    """
    out = wc_df.copy()
    out["DeltaNWC"] = out["NetWorkingCapital"].diff().fillna(out["NetWorkingCapital"])  # first year assumes build
    return out[["Year", "DeltaNWC"]]

def compute_cash_flows(income_df: pd.DataFrame, assumptions: dict, wc_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build cash flow statement from income statement and assumptions.

    Assumptions keys (examples):
      - capex_pct_revenue
      - debt_change_schedule: dict {year: amount}
      - equity_issue_schedule: dict {year: amount}
      - dividends_pct_net_income
    """
    df = income_df.copy()

    # Capex as % of Revenue (negative investing cash flow)
    df["Capex"] = -df["Revenue"] * assumptions.get("capex_pct_revenue", 0.05)

    # Working capital delta
    delta_wc = compute_working_capital_change(wc_df)
    df = df.merge(delta_wc, on="Year")

    # Operating Cash Flow: Net Income + Depreciation - ΔNWC
    df["OperatingCF"] = df["NetIncome"] + df["Depreciation"] - df["DeltaNWC"]

    # Investing Cash Flow: Capex (and placeholder for acquisitions if needed)
    df["InvestingCF"] = df["Capex"]  # acquisitions can be added later

    # Financing Cash Flow: Debt change + Equity issue - Dividends
    debt_sched = assumptions.get("debt_change_schedule", {})
    equity_sched = assumptions.get("equity_issue_schedule", {})
    dividends_pct = assumptions.get("dividends_pct_net_income", 0.0)

    df["Financing_DebtChange"] = df["Year"].map(debt_sched).fillna(0.0)
    df["Financing_EquityIssue"] = df["Year"].map(equity_sched).fillna(0.0)
    df["Dividends"] = -(df["NetIncome"] * dividends_pct)  # outflow

    df["FinancingCF"] = df["Financing_DebtChange"] + df["Financing_EquityIssue"] + df["Dividends"]

    # Net Change in Cash
    df["NetChangeInCash"] = df["OperatingCF"] + df["InvestingCF"] + df["FinancingCF"]

    return df[[
        "Year",
        "OperatingCF",
        "InvestingCF",
        "FinancingCF",
        "NetChangeInCash",
        "Capex",
        "Financing_DebtChange",
        "Financing_EquityIssue",
        "Dividends"
    ]]

# balance_sheet_utils.py
"""
Balance Sheet utilities for three-statement model.

Business role:
- Track assets, liabilities, and equity across forecast years.
- Link PP&E to Capex and Depreciation.
- Compute working capital accounts as % of Revenue/COGS.
- Track Debt, Equity, Retained Earnings, Dividends.
- Provide Shareholding Pattern table.
"""

import pandas as pd

def compute_working_capital_accounts(income_df: pd.DataFrame, assumptions: dict) -> pd.DataFrame:
    """
    Compute receivables, inventory, payables from % assumptions.

    Assumptions keys:
      - ar_pct_revenue
      - inv_pct_cogs
      - ap_pct_cogs
    """
    df = income_df.copy()
    df["AccountsReceivable"] = df["Revenue"] * assumptions.get("ar_pct_revenue", 0.12)
    df["Inventory"] = df["COGS"] * assumptions.get("inv_pct_cogs", 0.08)
    df["AccountsPayable"] = df["COGS"] * assumptions.get("ap_pct_cogs", 0.15)
    df["NetWorkingCapital"] = df["AccountsReceivable"] + df["Inventory"] - df["AccountsPayable"]
    return df[["Year", "AccountsReceivable", "Inventory", "AccountsPayable", "NetWorkingCapital"]]

def compute_balance_sheet(income_df: pd.DataFrame, cash_flow_df: pd.DataFrame, assumptions: dict, opening_balances: dict = None) -> pd.DataFrame:
    """
    Build a simple but complete balance sheet per year.

    Inputs:
      - income_df: must include Year, NetIncome, Depreciation, EBIT, Revenue, COGS
      - cash_flow_df: must include Year, NetChangeInCash, Capex, Financing_DebtChange, Financing_EquityIssue, Dividends
      - assumptions:
          ppne_opening, cash_opening, debt_opening, equity_opening
          ar_pct_revenue, inv_pct_cogs, ap_pct_cogs
      - opening_balances (optional override dict)

    Returns:
      DataFrame with Assets (Cash, AR, Inventory, PP&E), Liabilities (AP, Debt), Equity (ShareCapital, RetainedEarnings)
    """
    # Resolve openings
    cash_open = (opening_balances or {}).get("cash_opening", assumptions.get("cash_opening", 0.0))
    ppne_open = (opening_balances or {}).get("ppne_opening", assumptions.get("ppne_opening", 0.0))
    debt_open = (opening_balances or {}).get("debt_opening", assumptions.get("debt_opening", 0.0))
    equity_open = (opening_balances or {}).get("equity_opening", assumptions.get("equity_opening", 0.0))

    wc = compute_working_capital_accounts(income_df, assumptions)
    df = income_df.merge(cash_flow_df[["Year", "NetChangeInCash", "Capex", "Financing_DebtChange", "Financing_EquityIssue", "Dividends"]], on="Year")
    df = df.merge(wc, on="Year")

    # Initialize rolling accounts
    cash = []
    ppne = []
    debt = []
    share_capital = []
    retained_earnings = []

    current_cash = cash_open
    current_ppne = ppne_open
    current_debt = debt_open
    current_share_capital = equity_open  # initial paid-in capital
    current_retained = 0.0

    for _, row in df.iterrows():
        # Cash accumulates by net change in cash
        current_cash += row["NetChangeInCash"]

        # PP&E evolves with Capex and Depreciation
        current_ppne = max(0.0, current_ppne + row["Capex"] - row["Depreciation"])

        # Debt evolves by financing flows
        current_debt = max(0.0, current_debt + row["Financing_DebtChange"])

        # Equity: share capital + retained earnings
        current_share_capital = max(0.0, current_share_capital + row["Financing_EquityIssue"])
        current_retained = max(0.0, current_retained + row["NetIncome"] - row["Dividends"])

        cash.append(current_cash)
        ppne.append(current_ppne)
        debt.append(current_debt)
        share_capital.append(current_share_capital)
        retained_earnings.append(current_retained)

    out = pd.DataFrame({
        "Year": df["Year"],
        "Cash": cash,
        "AccountsReceivable": df["AccountsReceivable"],
        "Inventory": df["Inventory"],
        "PP&E": ppne,
        "TotalAssets": [c + ar + inv + p for c, ar, inv, p in zip(cash, df["AccountsReceivable"], df["Inventory"], ppne)],
        "AccountsPayable": df["AccountsPayable"],
        "Debt": debt,
        "ShareCapital": share_capital,
        "RetainedEarnings": retained_earnings,
    })

    out["TotalLiabilities"] = out["AccountsPayable"] + out["Debt"]
    out["TotalEquity"] = out["ShareCapital"] + out["RetainedEarnings"]
    out["AssetsMinusLiabEq"] = out["TotalAssets"] - (out["TotalLiabilities"] + out["TotalEquity"])  # Should be ~0

    return out

def compute_shareholding_pattern(balance_sheet_df: pd.DataFrame, ownership: dict) -> pd.DataFrame:
    """
    Generate a shareholding table by Year based on ShareCapital and ownership %.

    ownership: {"Promoters": 0.55, "Institutions": 0.35, "Public": 0.10}
    """
    pattern_rows = []
    for _, row in balance_sheet_df.iterrows():
        total_equity_value = row["TotalEquity"]
        year = row["Year"]
        for holder, pct in ownership.items():
            pattern_rows.append({
                "Year": year,
                "Holder": holder,
                "OwnershipPct": pct,
                "EquityAttributed": total_equity_value * pct
            })
    return pd.DataFrame(pattern_rows)

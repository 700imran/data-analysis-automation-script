import yfinance as yf

def safe_get(df, keys):
    """Try multiple possible row names, return first match or None."""
    for k in keys:
        if k in df.index:
            return df.loc[k]
    return None

def get_assumptions(ticker_symbol, rf=0.07, rm=0.12):
    t = yf.Ticker(ticker_symbol)

    fin = t.financials
    cf = t.cashflow
    bs = t.balance_sheet

    revenue = safe_get(fin, ["Total Revenue"])

    # Growth rate
    growth_rate = revenue.pct_change(fill_method=None).dropna().mean()


    # COGS %
    cogs = safe_get(fin, ["Cost Of Revenue"])
    cogs_pct = (cogs / revenue).mean() if (cogs is not None and revenue is not None) else None

    # Operating margin
    op_income = safe_get(fin, ["Operating Income", "EBIT"])
    op_margin = (op_income / revenue).mean() if (op_income is not None and revenue is not None) else None
    opex_pct = 1 - op_margin - cogs_pct if (op_margin and cogs_pct) else None

    # Tax rate
    tax_exp = safe_get(fin, ["Income Tax Expense"])
    ebt = safe_get(fin, ["Ebt", "Pretax Income"])
    tax_rate = (tax_exp / ebt).mean() if (tax_exp is not None and ebt is not None) else None

    # Capex %
    capex = safe_get(cf, ["Capital Expenditures", "Capital Expenditure"])
    capex_pct = (capex / revenue).mean() if (capex is not None and revenue is not None) else None

    # Depreciation %
    depr = safe_get(cf, ["Depreciation"])
    depr_pct = (depr / revenue).mean() if (depr is not None and revenue is not None) else None

    # Working Capital %
    curr_assets = safe_get(bs, ["Total Current Assets"])
    curr_liab = safe_get(bs, ["Total Current Liabilities"])
    wc = (curr_assets - curr_liab) if (curr_assets is not None and curr_liab is not None) else None
    wc_pct = (wc / revenue).mean() if (wc is not None and revenue is not None) else None

    # Discount rate (CAPM)
    beta = t.info.get("beta", 1)
    discount_rate = rf + beta * (rm - rf)

    return {
        "Growth Rate": round(growth_rate*100, 2) if growth_rate else "N/A",
        "COGS %": round(cogs_pct*100, 2) if cogs_pct else "N/A",
        "Opex %": round(opex_pct*100, 2) if opex_pct else "N/A",
        "Tax Rate": round(tax_rate*100, 2) if tax_rate else "N/A",
        "Capex %": round(capex_pct*100, 2) if capex_pct else "N/A",
        "Depreciation %": round(depr_pct*100, 2) if depr_pct else "N/A",
        "Working Capital %": round(wc_pct*100, 2) if wc_pct else "N/A",
        "Discount Rate (CAPM)": round(discount_rate*100, 2)
    }

if __name__ == "__main__":
    # Ask user for ticker when running script directly
    ticker = input("Enter ticker symbol (e.g., WMT, MSFT, JPM, TCS.NS): ").strip()
    assumptions = get_assumptions(ticker)
    print(f"Assumptions for {ticker}:")
    print(assumptions)



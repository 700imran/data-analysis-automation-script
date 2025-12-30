import pandas as pd
import yfinance as yf

def safe_get(df, keys):
    """Try multiple possible row names, return first match or None."""
    for k in keys:
        if k in df.index:
            return df.loc[k]
    return None


def get_industry_metrics(industry: str):
    """
    Fetch industry benchmark metrics using Yahoo Finance sector ETFs or representative tickers.
    Industry examples: 'Technology', 'Retail', 'Healthcare'
    Returns a dictionary of assumptions for financial_forecast.
    """
    industry_map = {
        "Technology": "XLK",
        "Retail": "XRT",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE"
    }

    if industry not in industry_map:
        raise ValueError(f"Industry '{industry}' not supported. Choose from {list(industry_map.keys())}")

    ticker = yf.Ticker(industry_map[industry])
    fin = ticker.financials
    cf = ticker.cashflow
    bs = ticker.balance_sheet

    # Revenue
    revenue = safe_get(fin, ["Total Revenue", "Revenue", "Net Sales"])
    if revenue is None:
        print("Revenue data not found — using fallback growth rate.")
        growth_rate = 0.05
    else:
        growth_rate = revenue.pct_change(fill_method=None).dropna().mean()

    # COGS %
    cogs = safe_get(fin, ["Cost Of Revenue", "Cost of Goods Sold"])
    cogs_pct = (cogs / revenue).mean() if (cogs is not None and revenue is not None) else 0.6

    # Operating margin
    op_income = safe_get(fin, ["Operating Income", "EBIT"])
    op_margin = (op_income / revenue).mean() if (op_income is not None and revenue is not None) else 0.2
    opex_pct = 1 - op_margin - cogs_pct if (op_margin and cogs_pct) else 0.2

    # Capex %
    capex = safe_get(cf, ["Capital Expenditures", "Capital Expenditure"])
    capex_pct = (capex / revenue).mean() if (capex is not None and revenue is not None) else 0.05

    # Depreciation %
    depr = safe_get(cf, ["Depreciation"])
    depr_pct = (depr / revenue).mean() if (depr is not None and revenue is not None) else 0.04

    # Working Capital %
    curr_assets = safe_get(bs, ["Total Current Assets"])
    curr_liab = safe_get(bs, ["Total Current Liabilities"])
    wc = (curr_assets - curr_liab) if (curr_assets is not None and curr_liab is not None) else None
    wc_pct = (wc / revenue).mean() if (wc is not None and revenue is not None) else 0.1

    return {
        "growth_rate": float(growth_rate),
        "cogs_pct": float(cogs_pct),
        "opex_pct": float(opex_pct),
        "capex_pct": float(capex_pct),
        "depr_pct": float(depr_pct),
        "wc_pct": float(wc_pct),
        "tax_rate": 0.30,
        "discount_rate": 0.12,
        "terminal_growth": 0.03
    }


def financial_forecast(
    revenue=1_000_000,
    growth_rate=0.10,
    cogs_pct=0.60,
    opex_pct=0.20,
    tax_rate=0.30,
    capex_pct=0.05,
    depr_pct=0.04,
    wc_pct=0.10,
    discount_rate=0.12,
    years=5,
    terminal_growth=0.03
):
    """Generate financial forecast and valuation metrics."""
    data = []
    for year in range(1, years + 1):
        rev = revenue * ((1 + growth_rate) ** year)
        cogs = rev * cogs_pct
        opex = rev * opex_pct
        depr = rev * depr_pct
        ebit = rev - cogs - opex - depr
        tax = ebit * tax_rate
        net_income = ebit - tax
        capex = rev * capex_pct
        wc_change = rev * wc_pct
        fcf = net_income + depr - capex - wc_change
        discounted_fcf = fcf / ((1 + discount_rate) ** year)

        data.append([
            year, rev, cogs, opex, depr, ebit, net_income,
            capex, wc_change, fcf, discounted_fcf
        ])

    df = pd.DataFrame(data, columns=[
        "Year", "Revenue", "COGS", "Opex", "Depreciation", "EBIT", "Net Income",
        "Capex", "Working Capital Change", "Free Cash Flow", "Discounted FCF"
    ])

    terminal_value = (df["Free Cash Flow"].iloc[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** years)

    enterprise_value = df["Discounted FCF"].sum() + discounted_terminal_value
    net_present_value = df["Free Cash Flow"].iloc[-1] * 0.10

    return df, round(enterprise_value, 2), round(net_present_value, 2)


def forecast_with_industry(revenue: float, years: int, industry: str):

    """
    Wrapper: get industry benchmarks and run forecast.
    """
    metrics = get_industry_metrics(industry)
    return financial_forecast(
        revenue=revenue,
        growth_rate=metrics["growth_rate"],
        cogs_pct=metrics["cogs_pct"],
        opex_pct=metrics["opex_pct"],
        tax_rate=metrics["tax_rate"],
        capex_pct=metrics["capex_pct"],
        depr_pct=metrics["depr_pct"],
        wc_pct=metrics["wc_pct"],
        discount_rate=metrics["discount_rate"],
        years=years,
        terminal_growth=metrics["terminal_growth"]
    )

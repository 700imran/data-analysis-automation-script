import os
import pandas as pd
import yfinance as yf

def valuation_kpis(ticker_symbol, gov_bond_yield=0.07):
    """
    Calculate valuation KPIs for a given company ticker.
    Returns a DataFrame with metrics.
    """
    t = yf.Ticker(ticker_symbol)
    info = t.info
    
    cmp = info.get("currentPrice")
    eps = info.get("trailingEps")
    bvps = info.get("bookValue")
    dividend = info.get("dividendRate")
    beta = info.get("beta", 1)
    
    # KPIs
    pe = cmp / eps if eps else None
    pb = cmp / bvps if bvps else None
    earnings_yield = eps / cmp if eps else None
    dividend_yield = dividend / cmp if dividend else None
    
    # Over/Under valuation check
    valuation_flag = "Undervalued" if earnings_yield and earnings_yield > gov_bond_yield else "Overvalued"
    
    return pd.DataFrame([{
        "Ticker": ticker_symbol,
        "CMP": cmp,
        "EPS": eps,
        "P/E": round(pe, 2) if pe else "N/A",
        "P/B": round(pb, 2) if pb else "N/A",
        "Earnings Yield (%)": round(earnings_yield*100, 2) if earnings_yield else "N/A",
        "Dividend Yield (%)": round(dividend_yield*100, 2) if dividend_yield else "N/A",
        "Gov Bond Yield (%)": gov_bond_yield*100,
        "Valuation": valuation_flag
    }])

def save_kpis(df, output_folder=r"C:\Users\Dell\Output", filename_base="valuation_kpis"):
    """
    Save KPI DataFrame into CSV and XLSX in output folder.
    Creates folder if missing. Only creates files if they don't exist.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    csv_path = os.path.join(output_folder, f"{filename_base}.csv")
    xlsx_path = os.path.join(output_folder, f"{filename_base}.xlsx")
    
    if not os.path.exists(csv_path):
        df.to_csv(csv_path, index=False)
        print(f"CSV file created: {csv_path}")
    else:
        print(f"CSV file already exists: {csv_path}")
    
    if not os.path.exists(xlsx_path):
        df.to_excel(xlsx_path, index=False)
        print(f"XLSX file created: {xlsx_path}")
    else:
        print(f"XLSX file already exists: {xlsx_path}")

# -------------------------------
# Script entry point
# -------------------------------
if __name__ == "__main__":
    ticker = input("Enter ticker symbol (e.g., WMT, MSFT, JPM, TCS.NS): ").strip()
    df = valuation_kpis(ticker)
    print(df.to_string(index=False))
    save_kpis(df)


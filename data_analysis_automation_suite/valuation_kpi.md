
---

## 📘 `valuation_kpi_utils.py` — Markdown Documentation

`markdown`
# Valuation KPI Generator

## Purpose
This script calculates key valuation metrics for public companies using `yfinance`, and flags whether a company is overvalued or undervalued based on earnings yield vs. government bond yield.

## Features
- Calculates:
  - P/E, P/B, EPS, CMP
  - Earnings Yield, Dividend Yield
  - Valuation flag (Overvalued/Undervalued)
- Saves results to `.csv` and `.xlsx` for Power BI auto-refresh
- Creates output folder if missing
- Interactive ticker input when run directly

## Usage in Notebook
```python
from valuation_kpi_utils import valuation_kpis

df = valuation_kpis("TCS.NS")
print(df)

# Financial Assumption Extraction Utility

## Purpose
This script extracts key financial modeling assumptions from live company data using `yfinance`. It supports robust fallback logic via `safe_get()` to handle missing rows and inconsistent labels across companies.

## Features
- Calculates:
  - Revenue growth rate
  - COGS %, Opex %, Tax rate
  - Capex %, Depreciation %, Working Capital %
  - Discount rate (CAPM)
- Defensive coding with `safe_get()` to avoid KeyErrors
- Modular function `get_assumptions(ticker)` for reuse in notebooks and pipelines

## Usage
```python
from financial_metrics_utils import get_assumptions

ticker = "TCS.NS"
assumptions = get_assumptions(ticker)
print(assumptions)

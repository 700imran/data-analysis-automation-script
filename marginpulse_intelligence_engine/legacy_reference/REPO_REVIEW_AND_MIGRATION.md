# Existing repository review and migration notes

Reviewed source: https://github.com/700imran/data-analysis-automation-script (default branch `main`, public repository at review time).

## Reusable intent retained

| Existing file | Original intent | New engine treatment |
|---|---|---|
| `primary_clean_utils.py` | General cleaning | Replaced with safe schema mapping, typed parsing, duplicate and missing-value visibility; no blanket zero-fill. |
| `analysis_utils.py` | Regression, correlation, group tests, plots | Retained as future/optional analytical capability; core management KPIs are deterministic grouped calculations with explicit data coverage. |
| `kpi_utils.py` | Public ticker valuation KPIs using yfinance | Excluded from operating-client default modules; equity valuation is not a distributor/retailer operating KPI. |
| `balance_sheet_utils.py` | Forecast working-capital and balance-sheet structure | Replaced with actuals-oriented receivables, payables and inventory visibility. Forecast balance-sheet assumptions are not mixed with client actuals. |
| `cashflow_utils.py` | Forecast cash flow statement | Not run as actual cash flow because source ledger coverage and accounting classification must first be confirmed. Payment/collection exports are included. |
| `forecast_utils.py` | Forecast and valuation model using Yahoo Finance sector data/fallback assumptions | Excluded from default service. Client-specific forecast requires approved assumptions, scenario inputs and evidence, not generic ETF benchmarks. |
| `task_runner.py` | Interactive orchestration | Replaced with configuration-driven CLI and FastAPI. |
| `output_utils.py` | Hardcoded output path and interactive save prompt | Replaced with client-isolated output folders, standard ZIP packaging and Power BI CSV exports. |

## Defects / risks found in the source reviewed

- `primary_clean_utils.clean_dataframe` fills every numeric null with zero; this can fabricate financial values and is not retained.
- `task_runner.py` imports `run_forecast` from `forecast_utils.py`, while the reviewed `forecast_utils.py` exposes `financial_forecast` and `forecast_with_industry`, not `run_forecast`.
- `task_runner.py` calls `valuation_kpis(df, predictors, target, ticker)`, while the reviewed `kpi_utils.valuation_kpis` accepts `ticker_symbol` and `gov_bond_yield`.
- `default_folder.py` uses `pd.read_excel` / `pd.read_csv` without importing pandas as `pd` in the reviewed file.
- `output_utils.py` uses a fixed Windows path and an interactive `input()` prompt, which are unsuitable for API/background processing.
- `analysis_target_entry.py` requires terminal input, which is unsuitable for repeatable API jobs.
- `forecast_utils.py` uses live Yahoo Finance sector tickers and fallback assumptions; this is not a validated benchmark source for an individual SME client.

These observations apply to the source files at the repository revision reviewed, not necessarily any later updates.

## Important implementation choice

The new engine is a clean configurable refactor. It does not import the old modules at runtime because their interactive prompts, fixed paths and inconsistent function contracts would undermine the API. Keep the original repository as a reference/legacy project until the new test suite and client-specific QA are accepted.

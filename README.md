 Data Analysis Automation Suite (Quick Guide)
1. Analysis Script (analysis_utils.py)
Call: prepare_regression(), check_correlation(), compare_groups(), plot_sales_by_group()

Guide: Run regression, correlation, hypothesis tests, and charts in one go.

Benefit: Fast statistical insights with reusable functions.

Loss: Needs clean input data; raw files may break workflows.

2. Clean Script (primary_clean_utils.py)
Call: clean_dataframe(df)

Guide: Standardize messy CSV/Excel into analysis‑ready DataFrames.

Benefit: Consistent inputs, fewer analyst errors.

Loss: Custom cleaning rules may miss edge cases.

3. Financial Metrics (financial_metrics_utils.py)
Call: get_assumptions("TCS.NS")

Guide: Pull growth, margins, tax, capex, WC, discount rate from live market data.

Benefit: Real‑time assumptions for valuation models.

Loss: Dependent on external APIs; missing labels need safe handling.

4. Forecast Script (forecast_utils.py)
Call: run_forecast()

Guide: Build 3‑statement model → EV & NPV outputs.

Benefit: 20% faster, 10–12% more accurate valuations.

Loss: Assumption quality drives accuracy; garbage in = garbage out.

5. Task Runner (task_runner.py)
Call: python task_runner.py

Guide: Orchestrates cleaning, analysis, KPI modeling, forecasting in one run.

Benefit: Saves 10–15 analyst hours/week, 70–80% faster workflows.

Loss: Heavy dependency on all modules; one failure can stop the pipeline.

📌 Business Takeaway
This suite automates analytics end‑to‑end, cutting cost and time while improving accuracy.

Upside: Speed, consistency, scalability.

Downside: Relies on clean data and stable APIs; requires maintenance for edge cases.

---

## Repository Map

| Path | What it is | Status |
|---|---|---|
| Root `*.py`, `*.ipynb`, `*.md` | Data Analysis Automation Suite (sections above) | Original content, unchanged |
| `marginpulse_intelligence_engine/` | MarginPulse Intelligence Engine v0.1.0: Python engine, FastAPI service, CLI, demo datasets, docs, tests | Prototype. 8 unit/API tests pass; see its `docs/SECURITY_AND_PRODUCTION_GATE.md` before any real client data or public deployment |
| `MarginPulse_Managed_Intelligence_Final_Launch_Kit/` | Service launch kit: brand assets, 15 templates/policies (`documents/`), static website, operations tracker, dummy data | Templates and drafts. Legal documents (NDA, agreement, privacy, terms) need review by a qualified professional before use |

All data in the launch kit's `dummy_data/` and the engine's `examples/` is synthetic. Never commit `.env` files or client data.

# MarginPulse Configurable Business Intelligence Engine

Version: 0.1.1 (pilot / controlled validation build)

A single configurable Python engine for distributors, retailers and selected service businesses. It reads CSV/XLSX datasets, maps different client column names into a canonical model, validates data, activates available analysis modules, creates traceable management findings and exports tidy CSV tables for Power BI.

This is a refactor/superset direction based on the user's existing repository:

- https://github.com/700imran/data-analysis-automation-script
- Reuses the intent of `primary_clean_utils.py`, `analysis_utils.py`, `kpi_utils.py`, `balance_sheet_utils.py`, `cashflow_utils.py`, `forecast_utils.py` and `task_runner.py` while replacing the interactive, hardcoded orchestration with a configurable engine.
- The legacy cleaner's behaviour of filling every numeric null with zero is intentionally not retained. Missing financial values remain missing unless a documented derivation is mathematically safe.
- Public-market valuation (`yfinance`) and forecast valuation models are not run on client operating data. They are not suitable as default distributor/retailer management analysis without explicit assumptions and source validation.

## What is included

- Canonical datasets: sales, purchases, expenses, inventory movements/snapshots, receivables, payables, payments, products, customers, suppliers, service projects and timesheets.
- Column mapping using aliases, plus per-client mapping overrides.
- XLSX multi-sheet and CSV ingestion.
- Dataset discovery using file/sheet names, plus explicit `dataset_map` override.
- Data-quality report: unmapped columns, required fields, missing counts and duplicates.
- Interconnected analysis: sales, purchasing, inventory, receivables/payables and dimensions linked using product/customer/supplier IDs.
- Profile presets: auto, distributor, retailer, service.
- Rule-based findings with evidence, recommended action and limitations.
- Interconnected checks: sales-to-receivables invoice values, paid amounts-to-payment register, inventory snapshot-to-movement ledger, and source gross profit-to-recomputed gross profit.
- Business modules: financial performance, sales, product/customer/category profitability, costs, inventory, receivables, payables, working-capital visibility, collections, procurement, retail stores, service projects and workforce utilisation.
- FastAPI upload and download API, CLI runner and Power BI CSV exports.
- Synthetic distributor test workbook and test suite.

## Profiles

### Distributor
Recommended input: Sales, Purchases, Expenses, Inventory_Summary or Inventory_Movements, Receivables, Payables, Products, Customers, Suppliers and Payments.

### Retailer
Uses the same core tables. Add `store_id`/`store_name` to Sales, Expenses and Inventory to unlock store performance. The engine does not require a separate retailer codebase.

### Service
Uses Sales (or service revenue in a sales-like ledger), Expenses, Customers and optionally Service_Projects and Timesheets. Projects and utilisation analysis only appear when those structured datasets exist. Highly bespoke project accounting schemas may need explicit mapping or a separate adapter.

## Quick start (Windows PowerShell)

```powershell
cd marginpulse_intelligence_engine
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a long random `MARGINPULSE_API_KEY`. Set it in the shell before starting the API:

```powershell
$env:MARGINPULSE_API_KEY="your-long-random-secret"
$env:MARGINPULSE_STORAGE=".\storage"
uvicorn marginpulse_engine.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. Supply `X-API-Key` for protected endpoints.

## Run the included distributor example

```powershell
python -m marginpulse_engine.cli --files examples/distributor_demo.xlsx --client-id demo-uae-distributor --profile distributor --currency AED --country UAE --as-of-date 2026-10-31 --output-root .\storage
```

The included synthetic distributor workbook exercises the distributor pipeline. Its figures reconcile across sales, receivables, payments and the inventory ledger. Two deliberate data-integrity exceptions remain for demonstration: four products have negative closing stock, and supplied expenses are about 10x gross profit (synthetic data, not a realistic cost base). The engine flags both rather than adjusting the source figures.

The engine writes:

```text
storage/<client_id>/<analysis_id>/
  analysis.json
  manifest.json
  normalized_data/*.csv
  powerbi_export/*.csv
storage/<client_id>/<analysis_id>.zip
```

The output ZIP contains canonicalised data and analytical exports. Treat it as confidential client material. It deliberately excludes the original uploaded file; preserve the original in your controlled source archive if your contract and retention policy require it.

## API

### Health
`GET /health` (no key)

### Modules and profiles
`GET /api/v1/modules` with `X-API-Key`.

### Analyse uploads
`POST /api/v1/analyze` multipart form:
- `files`: one or more `.csv`, `.xlsx` or `.xlsm` files. An XLSX file may contain multiple recognised sheets.
- `config`: JSON string.
- `X-API-Key`: header.

Example config:

```json
{
  "client_id": "uae-distributor-001",
  "profile": "distributor",
  "country": "UAE",
  "currency": "AED",
  "as_of_date": "2026-10-31",
  "thresholds": {
    "revenue_decline_pct": 10,
    "margin_decline_pp": 2,
    "overdue_share_pct": 30
  },
  "column_mappings": {
    "sales": {"revenue": "Sales Value", "transaction_date": "Txn Dt"}
  },
  "dataset_map": {"export.xlsx::Sheet1": "sales"}
}
```

- `GET /api/v1/analyses/{analysis_id}?client_id=...`
- `GET /api/v1/analyses/{analysis_id}/download?client_id=...`

## Config behaviour

- `profile` is a reporting/business context label; data availability and validated fields determine which analytical capabilities are calculated.
- `dataset_map` maps `filename::sheet`, sheet name or filename to a canonical entity when auto-detection is ambiguous.
- `column_mappings` maps canonical field names to exact source column names per dataset.
- `thresholds` controls alert thresholds; default values are screening rules, not industry benchmarks.
- `currency` labels output values. No foreign-exchange conversion is performed. Do not combine multi-currency records without a separate, dated FX conversion process.
- `dayfirst` (default `true`) controls how ambiguous dates such as 05/10/2026 are read (5 October). Set `false` for month-first sources. ISO dates (2026-10-05) are unaffected.
- `as_of_date` determines receivables/payables ageing and inventory review dates. Use the client's reporting cut-off, not the machine date.

## Interconnected model

See `docs/CANONICAL_DATA_MODEL.md` and `docs/POWER_BI_MODEL.md`.

Relationships are based on stable identifiers:

- Sales / Purchases / Inventory ↔ Products via `product_id`.
- Sales / Receivables ↔ Customers via `customer_id`.
- Purchases / Payables ↔ Suppliers via `supplier_id`.
- Payments ↔ invoice/party identifiers.
- Service projects ↔ customers and timesheets via `project_id`.

If a source does not provide stable IDs, it can still be analysed at transaction level, but joins and entity-level insights are limited. Names are not treated as guaranteed unique keys.

## Tests

The package includes 15 automated tests covering distributor, retailer and service examples, dynamic column overrides, missing-cost safety, protected API access, upload and ZIP download, plus regression tests that compare engine totals with independently calculated figures. Run:

```bash
pytest -q
```

## Important limitations / production gate

This is an executable pilot engine, not a production multi-tenant SaaS deployment.

Before processing live client data in a hosted environment, implement and independently test:

1. Tenant identity, per-client authorisation and storage/database row-level security (the included API key is a single service key, not per-client identity).
2. TLS, managed secrets, private storage, malware scanning, file-size/row-count limits and audit retention.
3. Job queue, cancellation, retry/idempotency, monitoring and backups.
4. Client-specific data retention/deletion and contract-approved sub-processors.
5. Reconciliation tests and accountant/finance-owner sign-off for every metric used in commercial reports.
6. Power BI external sharing/embedding licensing and row-level security. The CSV export is Power BI-ready; this package does not provision a Power BI tenant, semantic model or paid embedding capacity.

Do not send confidential client data to external AI services in this version. Findings are deterministic rules and calculations. Recommendations are management review prompts, not guaranteed savings, accounting opinions or investment advice.

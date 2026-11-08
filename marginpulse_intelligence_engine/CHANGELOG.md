# Changelog

## 0.1.1 – Accuracy review fixes

- Fixed header matching for all-caps source columns (e.g. `COGSAED`, `UnitSellingPriceAED`); source cost-of-goods is now used instead of a derived value, removing false gross-profit mismatches.
- Reconciliation: corrected `matched_rows` count, tightened invoice/payment tolerance from 1.00 to 0.05 and gross-profit tolerance to 0.015, added a negative-closing-stock check.
- Negative stock is reported separately (`INV_NEG_001`) and no longer counted as "below reorder level".
- Purchase price findings now use quantity-weighted, product-level costs across suppliers and only compare consecutive months (the earlier logic could compare different suppliers).
- New findings: `OPEX_COVER_001` (expenses exceed gross profit) and `DQ_DUP_001` (duplicate rows, which are not removed).
- Dates now default to day-first (`dayfirst` config option).
- Added regression tests.
- Indian accounting-export support: aliases for Tally/Busy-style headers (VoucherDate, TaxableValue, ItemCode, PartyCode, ExpenseHead, GSTAmount and similar); GST-inclusive receivables now reconcile to sales plus supplied GST.
- Duplicate detection now uses all source columns (unmapped voucher numbers no longer cause false duplicates).
- Loud warnings when required fields are not mapped (`DQ_REQUIRED_001`) or revenue had to be derived (`DQ_DERIVED_REV_001`); previously these were silent.
- New finding `AR_CUST_001` (one customer holds a large share of overdue receivables).
- Added `examples/indian_distributor_demo.xlsx` and config (synthetic, fictional INR distributor).

## 0.1.0 – Initial configurable pilot engine

- Canonical data schemas and adaptable aliases for distributor, retailer and selected service datasets.
- CSV/XLSX ingestion, sheet detection and explicit schema/dataset overrides.
- Conservative numeric/date parsing and missing-value preservation.
- Sales, financial, cost, inventory, working-capital, receivables, payables, procurement, collection, store, product profitability, service project and workforce analysis.
- Cross-ledger reconciliation checks.
- Rule-based management insights with evidence and limitations.
- FastAPI API, CLI and Power BI CSV exports.
- Synthetic distributor, retailer and service workbooks.
- Automated tests for core profiles and API upload/download.

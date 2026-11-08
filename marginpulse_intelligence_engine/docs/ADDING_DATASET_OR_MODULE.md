# Extending the engine without client-specific hardcoding

## First choice: add configuration, not code

When a client uses a new column name, use `column_mappings` in that client's configuration. When a workbook uses unusual sheet names, use `dataset_map`. Save the approved mapping in the client's versioned configuration so the next reporting cycle reuses it.

Example:

```json
{
  "dataset_map": {"finance_export.xlsx::Tab 4": "sales"},
  "column_mappings": {
    "sales": {
      "transaction_date": "Posting Dt",
      "invoice_id": "Reference",
      "customer_id": "Party Code",
      "revenue": "Net Amount",
      "cogs": "Cost Amount"
    }
  }
}
```

## Add a reusable field alias

1. Edit `FIELD_ALIASES` in `marginpulse_engine/registry.py`.
2. Add an alias only when its meaning matches the canonical field; avoid ambiguous terms such as generic `value` where a dataset may have multiple values.
3. Add a mapping test using the new source column.
4. Confirm date/numeric parsing and data-quality output.

## Add a canonical dataset

1. Define dataset aliases in `DATASET_ALIASES`.
2. Define canonical fields and aliases in `FIELD_ALIASES`.
3. Set minimum required fields in `REQUIRED_FIELDS`.
4. Add the entity to `docs/CANONICAL_DATA_MODEL.md`.
5. Add fixture data and tests.
6. If the entity is linked, define its stable keys and relationship rules. Do not join on names unless the user explicitly approves a matching policy.

## Add a reusable analytical module

1. Add module name and requirements to `MODULES`.
2. Implement one deterministic calculator in `analysis.py`.
3. Return numeric findings, grain-level tables and coverage/limitations.
4. Wire the calculator into `engine.analyze_frames`.
5. Add thresholds only as configurable screening rules; do not label defaults as industry benchmarks.
6. Add tests for normal, partial and missing data.
7. Confirm its output is exported to `analysis.json` and Power BI CSVs.

## Industry pack approach

Prefer profile configuration over duplicated code:

- Distributor pack: purchase cost, supplier, product, stock, credit and collections.
- Retailer pack: store/location, basket, products, stock and sales channel.
- Service pack: sales-like revenue, expenses, project register and timesheets.

Only create a new reusable module when a real operating workflow requires data and calculations not expressible through existing canonical entities. One-off client fields should stay in mapping/configuration, not become an engine branch.

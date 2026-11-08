# API Usage Examples

Start locally after installing requirements and setting `MARGINPULSE_API_KEY` in `.env`.

## Health

```bash
curl http://127.0.0.1:8000/health
```

## Discover modules

```bash
curl -H "X-API-Key: YOUR_SECRET" http://127.0.0.1:8000/api/v1/modules
```

## Upload a workbook

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "X-API-Key: YOUR_SECRET" \
  -F 'config={"client_id":"uae-distributor-01","profile":"distributor","country":"UAE","currency":"AED","as_of_date":"2026-10-31"}' \
  -F 'files=@examples/distributor_demo.xlsx'
```

The response contains module availability, result payloads, insights, data quality and a download URL. Download with the same API key. The returned analysis ID is unique per run.

## Custom column mapping

```json
{
  "client_id": "client-india-02",
  "profile": "retailer",
  "country": "India",
  "currency": "INR",
  "as_of_date": "2026-10-31",
  "dataset_map": {"POS Export.xlsx::Tab 2": "sales"},
  "column_mappings": {
    "sales": {
      "transaction_date": "Txn Dt",
      "invoice_id": "Bill Ref",
      "customer_id": "Party Code",
      "product_id": "Item Ref",
      "quantity": "Units Sold",
      "revenue": "Net Value",
      "cogs": "Cost Value",
      "store_id": "Outlet Code"
    }
  }
}
```

Mapping overrides are exact source column names. If the engine cannot map a required field, it records an incomplete dataset rather than silently guessing.

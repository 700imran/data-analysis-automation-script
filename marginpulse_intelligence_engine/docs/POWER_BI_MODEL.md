# Power BI Model Guide

The engine exports canonical CSV tables under `normalized_data/` plus tidy analysis outputs under `powerbi_export/`.

## Recommended star schema

- `DimDate[Date]` → `FactSales[transaction_date]` (1:*; single direction)
- `DimDate[Date]` → `FactPurchases[transaction_date]`
- `DimDate[Date]` → `FactExpenses[transaction_date]`
- `DimProduct[product_id]` → sales, purchases and inventory fact `product_id`
- `DimCustomer[customer_id]` → sales and receivables `customer_id`
- `DimSupplier[supplier_id]` → purchases and payables `supplier_id`
- `DimStore[store_id]` → sales, expenses and inventory when supplied

Keep invoice-level facts separate. Avoid joining Sales directly to Receivables or Payments as many-to-many transaction joins can multiply totals. Use invoice ID bridge tables or aggregate payment/receivable facts to invoice grain before combining.

## Suggested starter DAX measures

```DAX
Revenue = SUM(FactSales[revenue])

COGS = SUM(FactSales[cogs])

Gross Profit = [Revenue] - [COGS]

Gross Margin % = DIVIDE([Gross Profit], [Revenue])

Operating Expenses = SUM(FactExpenses[amount])

Gross Profit Less Supplied Expenses = [Gross Profit] - [Operating Expenses]

Outstanding Receivables = SUM(FactReceivables[outstanding_amount])

Outstanding Payables = SUM(FactPayables[outstanding_amount])

Inventory Value = SUM(FactInventorySnapshot[inventory_value])
```

Label the `Gross Profit Less Supplied Expenses` measure carefully. It is not a complete operating profit measure unless all expenses, other income/expense, depreciation, tax and accounting adjustments are represented on a consistent basis.

## Client isolation

Create a separate client workspace/dataset per client for the initial service. If consolidating into a shared semantic model later, use a tenant key on every fact and dimension, validated row-level security, deny-by-default access and independent penetration tests. Do not rely on a hidden report filter for confidentiality.

This ZIP does not create or publish a Power BI semantic model. It exports the data and provides the modelling guide.

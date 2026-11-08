# Synthetic distributor dataset — usage notes

**Entity:** Fictional UAE general trading / distribution business (all data is synthetic).  
**Currency:** AED.  
**Coverage:** 1 November 2025 to 31 October 2026.  
**Reporting cut-off:** 31 October 2026.

## Workbook sheets

- `ReadMe` — dataset context and limitations.
- `Products` — product master and synthetic standard price / cost / reorder fields.
- `Customers` — customer master and payment terms.
- `Suppliers` — supplier master.
- `Sales` — one row per invoice product line.
- `Purchases` — one row per purchase-order product line.
- `Expenses` — monthly synthetic category totals.
- `Inventory_Movements` — opening, purchase, sale and adjustment movements.
- `Inventory_Summary` — quantity roll-forward and simple movement flags at cut-off.
- `Receivables` — one row per invoice with paid / outstanding and ageing as at cut-off.
- `Payments` — synthetic receipts linked to invoices.
- `Data_Dictionary` — field descriptions and analytical cautions.

## Reconciliation rules

- `Sales.NetSalesAED` grouped by `InvoiceID` reconciles to `Receivables.InvoiceAmountAED`.
- `Payments.AmountAED` grouped by `InvoiceID` reconciles to `Receivables.AmountPaidAED`.
- `Receivables.OutstandingAED` equals invoice amount less amount paid.
- `Inventory_Summary.ClosingQty` equals opening + received - sold + adjustments.
- `Inventory_Movements.QuantityChange` uses positive quantities for stock receipts and negative quantities for sales issues.

## Important limitations

- Fictitious entity, product, customer, supplier and transaction data only.
- Values are synthetic and are not market prices or actual commercial records.
- Product standard costs are not landed costs, moving-average costs or an audited inventory valuation.
- Expenses are monthly category totals, not transaction-level invoices.
- Synthetic receipts simplify payment allocation to one receipt per invoice.
- No VAT return, accounting ledger, cash flow statement or tax calculation is represented.
- Use the dataset to test mapping, joins, validation, calculations and report formatting only.

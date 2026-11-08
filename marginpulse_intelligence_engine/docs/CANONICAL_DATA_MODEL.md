# Canonical Data Model

The engine standardises source exports to the following entities. It does not require every entity for every client.

| Canonical entity | Core fields | Main relationships |
|---|---|---|
| sales | transaction_date, invoice_id, customer_id/name, product_id/name, quantity, unit_price, revenue, discount, cogs, store_id | product, customer, store, date |
| purchases | transaction_date, purchase_id, supplier_id/name, product_id/name, quantity, unit_cost, purchase_value | product, supplier, date |
| expenses | transaction_date, expense_id, category, amount, department, store_id | date, store, cost category |
| inventory_movements | transaction_date, movement_type, reference_id, product_id, quantity_delta, unit_cost, location_id | product, location, date |
| inventory_snapshot | snapshot_date, product_id/name, opening/received/sold/adjustment/closing quantity, reorder_level, unit_cost, inventory_value, last_sale_date | product, date, location if supplied |
| receivables | invoice_id, invoice_date, customer_id/name, due_date, invoice_amount, paid_amount, outstanding_amount | customer, invoice, date |
| payables | invoice_id, invoice_date, supplier_id/name, due_date, invoice_amount, paid_amount, outstanding_amount | supplier, invoice, date |
| payments | transaction_date, payment_id, invoice_id, party_id/name/type, amount, direction | invoice, party, date |
| products | product_id, product_name, category, unit, unit_cost, selling_price, reorder_level | product dimension |
| customers | customer_id, customer_name, segment, region, credit_limit, payment_terms_days | customer dimension |
| suppliers | supplier_id, supplier_name, category, region, payment_terms_days | supplier dimension |
| service_projects | project_id/name, customer_id/name, dates, project_revenue, project_cost, status, hours | customer, project, date |
| timesheets | project_id, employee_id/name, work_date, hours, billable_hours, hourly_cost, billable_amount | project, employee, date |

## Data integrity rules

- Stable IDs are preferred. Names may be non-unique and are not a guaranteed join key.
- Dates are parsed but invalid dates remain null and are reported.
- Currency is a client-level output label. This release does not perform FX conversion.
- Financial nulls remain null. A missing cost is not a zero cost.
- Derived revenue is only calculated when quantity and unit price exist (and discount is applied only when supplied).
- Derived COGS is only calculated when quantity and unit cost exist.
- An operating result is labelled as gross profit less supplied expenses and is not represented as a complete operating profit unless the full cost basis is confirmed.
- Inventory movements can create a stock snapshot by summing signed quantities per product. That derived closing balance is only reliable when the movement ledger includes a valid opening balance and all subsequent movements.
- Receivables/payables ageing uses the supplied due date and outstanding amount at `as_of_date`.

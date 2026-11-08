# MarginPulse Operations Control Centre

`MarginPulse_Operations_Control_Centre.xlsx` is the recommended single source of truth for daily internal operations. It is brand-styled in the MarginPulse navy / teal / emerald palette and includes dropdowns, date formats, filtered register tables, a dashboard and a pre-launch checklist.

## Tabs

1. **Dashboard** — lead, client, delivery and collection indicators.
2. **Leads** — prospect master with source URL, decision-maker, verification, stage and next follow-up.
3. **Interactions** — one row per actual outreach or conversation; distinguish attempts from responses.
4. **Client Register** — legal counterparty, provider identity, agreement/NDA/SOW status and access details.
5. **Proposals** — scope, setup fee, recurring fee, currency, status and decision.
6. **Projects** — reporting cycles, deadlines, status and QA handoff.
7. **Data Register** — metadata about files received; do not put source financial records in this workbook.
8. **Data Quality** — validation checks, results, severity, corrective action and evidence.
9. **Report QA** — release checklist and final approval.
10. **Delivery Log** — report versions, recipients, delivery channel and acknowledgement.
11. **Invoices** — invoice, due date, payment status and overdue-day formula.
12. **Feedback** — client feedback, requested action and closure.
13. **Renewals** — contract end, notice deadline and renewal decisions.
14. **Incidents** — data, service, privacy, security and commercial incidents.
15. **Access & Deletion** — access approvals, expiry, revocation and deletion evidence.
16. **How to Use** — workflow instructions and control rules.
17. **Launch Checklist** — 18 pre-launch tasks with status dropdowns and live progress counts.

## Operating rules

- Use generated IDs (for example `LD-2026-0001`, `CL-0001`, `PRJ-CL0001-202611`) and link records by IDs, not only by company name.
- The Operations Control Centre is the preferred active CRM. Avoid entering the same lead separately in this file and the stand-alone Lead CRM template.
- Keep original client data in a separate, restricted client workspace. This workbook stores metadata and process status only.
- Amounts in different currencies must not be summed as one cash figure without a documented FX conversion. The dashboard's paid-invoice total is a raw entered-currency total and is not a consolidated converted amount.
- Keep evidence references and next actions current. A blank status is not proof that a task is complete.

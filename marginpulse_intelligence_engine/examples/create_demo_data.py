"""Generate small synthetic retailer and service-company workbooks for smoke testing."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

retail_sales = pd.DataFrame([
    ["2026-10-01", "R-001", "C-01", "P-01", "Cola 1L", 10, 8.0, 80.0, 48.0, "STORE-01"],
    ["2026-10-02", "R-002", "C-02", "P-02", "Rice 5kg", 4, 35.0, 140.0, 112.0, "STORE-01"],
    ["2026-09-01", "R-003", "C-01", "P-01", "Cola 1L", 20, 8.0, 160.0, 96.0, "STORE-02"],
    ["2026-09-02", "R-004", "C-03", "P-03", "Soap", 30, 5.0, 150.0, 90.0, "STORE-02"],
], columns=["Txn Date", "Receipt No", "Customer Code", "SKU", "Product Description", "Units", "Selling Price", "Net Sales", "Cost of Goods Sold", "Store"])
retail_purchases = pd.DataFrame([
    ["2026-10-01", "PO-1", "SUP-01", "P-01", "Cola 1L", 100, 4.8, 480.0],
    ["2026-09-01", "PO-2", "SUP-01", "P-01", "Cola 1L", 100, 4.5, 450.0],
], columns=["Purchase Date", "PO Number", "Supplier Code", "SKU", "Item", "Qty", "Cost Price", "Purchase Amount"])
retail_expenses = pd.DataFrame([
    ["2026-09-30", "Rent", 5000, "STORE-01"], ["2026-10-31", "Rent", 5200, "STORE-01"],
    ["2026-10-31", "Utilities", 900, "STORE-02"],
], columns=["Expense Date", "Expense Category", "Amount", "Branch"])
retail_inventory = pd.DataFrame([
    ["P-01", "Cola 1L", 40, 100, 30, 110, 50, 4.8, 528],
    ["P-02", "Rice 5kg", 20, 50, 4, 66, 30, 28, 1848],
], columns=["SKU", "Item Name", "Opening Stock", "Stock In", "Stock Out", "Closing Stock", "Minimum Stock", "Cost Price", "Stock Value"])
with pd.ExcelWriter(ROOT / "retailer_demo.xlsx", engine="openpyxl") as xw:
    retail_sales.to_excel(xw, sheet_name="Sales", index=False)
    retail_purchases.to_excel(xw, sheet_name="Purchases", index=False)
    retail_expenses.to_excel(xw, sheet_name="Expenses", index=False)
    retail_inventory.to_excel(xw, sheet_name="Inventory Summary", index=False)

service_sales = pd.DataFrame([
    ["2026-09-05", "S-001", "CL-01", "Website support", 1, 25000],
    ["2026-10-05", "S-002", "CL-02", "Implementation", 1, 40000],
], columns=["Date", "Invoice No", "Client ID", "Service Description", "Qty", "Revenue"])
service_expenses = pd.DataFrame([
    ["2026-09-30", "Contractor", 9000], ["2026-10-31", "Contractor", 12500],
], columns=["Expense Date", "Expense Category", "Amount"])
projects = pd.DataFrame([
    ["PR-01", "Website support", "CL-01", "2026-09-01", "2026-09-30", 25000, 12000, "Completed", 40],
    ["PR-02", "Implementation", "CL-02", "2026-10-01", "2026-10-31", 40000, 22000, "Completed", 72],
], columns=["Project ID", "Project Name", "Customer ID", "Start Date", "End Date", "Project Revenue", "Project Cost", "Status", "Hours"])
timesheets = pd.DataFrame([
    ["PR-01", "EMP-1", "2026-09-04", 20, 16, 150],
    ["PR-02", "EMP-2", "2026-10-04", 40, 32, 180],
], columns=["Project ID", "Employee ID", "Work Date", "Hours Worked", "Billable Hours", "Hourly Cost"])
with pd.ExcelWriter(ROOT / "service_demo.xlsx", engine="openpyxl") as xw:
    service_sales.to_excel(xw, sheet_name="Sales", index=False)
    service_expenses.to_excel(xw, sheet_name="Expenses", index=False)
    projects.to_excel(xw, sheet_name="Service Projects", index=False)
    timesheets.to_excel(xw, sheet_name="Timesheets", index=False)
print("Generated retailer_demo.xlsx and service_demo.xlsx")

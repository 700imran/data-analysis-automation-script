import os, glob, pandas as pd

def get_latest_data(folder=r"C:\Users\Dell\Documents\Data Analysis Input"):
    files = glob.glob(os.path.join(folder, "*.xlsx")) + glob.glob(os.path.join(folder, "*.csv"))
    if not files:
        raise FileNotFoundError("No .xlsx or .csv files found")
    latest = max(files, key=os.path.getctime)
    print("Picked file:", latest)
    return pd.read_excel(latest) if latest.endswith(".xlsx") else pd.read_csv(latest)

# Example use inside notebook
from latest_data_utils import get_latest_data
df = get_latest_data()
df.head()

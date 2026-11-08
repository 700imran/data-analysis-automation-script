import pandas as pd
import numpy as np
import scipy
import statsmodels
import sklearn
import openpyxl
import yfinance as yf

# Utilities
from latest_data_utils import get_latest_data
from primary_clean_utils import clean_dataframe
from default_folder import load_file
from analysis_target_entry import ask_for_columns
from analysis_utils import prepare_regression, check_correlation, compare_groups
from kpi_utils import valuation_kpis
from forecast_utils import run_forecast

from output_utils import save_output


def run_task(task: str,
             filepath: str = None,
             domain: str = None,
             assumptions: dict = None,
             opening_balances: dict = None,
             ownership: dict = None):
    """
    Universal runner (NO SCHEMA, NO AUTO-CONFIG)
    Tasks:
        - clean
        - scenario
        - relation
        - comparison
        - kpi
        - model
    """

    # Normalize task input
    task = (task or "").strip().lower()

    # -------------------------
    # Step 1: Load file
    # -------------------------
    if filepath is None:
        df = get_latest_data()
        print("✅ Auto-selected latest file")
    else:
        df = load_file(filepath)
        print(f"✅ Loaded file: {filepath}")

    # -------------------------
    # Step 2: Basic cleaning ONLY
    # -------------------------
    df = clean_dataframe(df)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    if df.shape[0] == 0:
        print("❌ Dataset is empty after basic cleaning.")
        return

    # -------------------------
    # CLEAN ONLY
    # -------------------------
    if task == "clean":
        save_output(df, filepath, "clean")
        print("✅ Clean results saved.")
        return

    # -------------------------
    # SCENARIO ANALYSIS (Regression)
    # -------------------------
    if task == "scenario":
        print("\nAvailable columns:", df.columns.tolist())
        predictors, target = ask_for_columns(df)
        reg = prepare_regression(df, predictors, target)
        df["scenario_prediction"] = reg.fittedvalues
        save_output(df, filepath, "scenario")
        print("✅ Scenario analysis saved.")
        return

    # -------------------------
    # RELATION FINDING (Correlation)
    # -------------------------
    if task == "relation":
        print("\nAvailable columns:", df.columns.tolist())
        predictors, target = ask_for_columns(df)
        corr, p = check_correlation(df, predictors[0], target)
        df["correlation_value"] = corr
        df["correlation_p"] = p
        save_output(df, filepath, "relation")
        print("✅ Relation results saved.")
        return

    # -------------------------
    # REASON FINDING (Hypothesis / A/B)
    # -------------------------
    if task == "comparison":
        print("\nAvailable columns:", df.columns.tolist())
        group_col = input("Enter grouping column: ").strip()
        metric = input("Enter metric column: ").strip()
        group_values = df[group_col].dropna().unique().tolist()
        print("Detected groups:", group_values)
        group_a = input("Enter first group value: ").strip()
        group_b = input("Enter second group value: ").strip()
        t, p = compare_groups(df, group_col, metric, group_a, group_b)
        df["t_value"] = t
        df["t_p"] = p
        save_output(df, filepath, "comparison")
        print("✅ Comparison results saved.")
        return

    # -------------------------
    # KPI VALUATION
    # -------------------------
    if task == "kpi":
        print("\nAvailable columns:", df.columns.tolist())
        predictors, target = ask_for_columns(df)
        ticker = input("Enter market ticker (e.g., WMT): ").strip()
        kpi_df = valuation_kpis(df, predictors, target, ticker)
        save_output(kpi_df, filepath, "kpi")
        print("✅ KPI results saved.")
        return

    # -------------------------
    # 3-STATEMENT MODEL
    # -------------------------
    if task == "model":
        
         # ✅ Just delegate to forecast_utils
        results = run_forecast(filepath=filepath, ownership=ownership)
        return results

    # -------------------------
    # UNKNOWN TASK
    # -------------------------
    print("⚠️ Unknown task. Choose: clean, scenario, relation, comparison, kpi, model.")

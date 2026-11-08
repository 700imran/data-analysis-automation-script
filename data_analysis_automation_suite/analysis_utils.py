#analysis_utils.py
import pandas as pd
import statsmodels.api as sm
from scipy.stats import pearsonr, ttest_ind
import matplotlib.pyplot as plt

# 1. Regression
def prepare_regression(df, predictors, target):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    predictors = [p.lower().replace(" ", "_") for p in predictors]
    target = target.lower().replace(" ", "_")
    
    df = df[predictors + [target]].dropna()
    X = df[predictors].astype(float)
    y = df[target].astype(float)
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return model

# 2. Correlation
def check_correlation(df, col1, col2):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    col1, col2 = col1.lower().replace(" ", "_"), col2.lower().replace(" ", "_")
    x = pd.to_numeric(df[col1], errors="coerce")
    y = pd.to_numeric(df[col2], errors="coerce")
    mask = x.notna() & y.notna()
    return pearsonr(x[mask], y[mask])

# 3. Hypothesis Testing
def compare_groups(df, group_col, value_col, group1, group2):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    group_col, value_col = group_col.lower().replace(" ", "_"), value_col.lower().replace(" ", "_")
    g1 = pd.to_numeric(df[df[group_col] == group1][value_col], errors="coerce").dropna()
    g2 = pd.to_numeric(df[df[group_col] == group2][value_col], errors="coerce").dropna()
    return ttest_ind(g1, g2)

# 4. Charting
def plot_sales_by_group(df, group_col, value_col):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    group_col, value_col = group_col.lower().replace(" ", "_"), value_col.lower().replace(" ", "_")
    grouped = df.groupby(group_col)[value_col].sum()
    grouped.plot(kind="bar", color="skyblue")
    plt.title(f"Total {value_col.replace('_',' ').title()} by {group_col.title()}")
    plt.ylabel(value_col.replace("_"," ").title())
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

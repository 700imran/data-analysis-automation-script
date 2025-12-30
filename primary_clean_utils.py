import pandas as pd

def clean_dataframe(df):
    """
    General-purpose cleaning function for any DataFrame.
    Steps:
    1. Normalize column names (lowercase, replace spaces with underscores).
    2. Strip whitespace from string values.
    3. Drop duplicate rows.
    4. Handle missing values (optional: fill with 0 or drop).
    5. Convert numeric-looking columns to numeric dtype.
    """
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Strip whitespace from string columns only
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # Drop duplicates
    df = df.drop_duplicates()

    # Drop fully empty rows
    df = df.dropna(how="all")

    # Fill numeric NA with 0
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(0)

    # Convert numeric-looking columns safely
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            pass

    return df




DEFAULT_FOLDER = r"C:\Users\Dell\Documents\Data Analysis Input"

def load_file(filepath):
    # If user gives only file name → attach default folder
    if "\\" not in filepath and "/" not in filepath:
        filepath = DEFAULT_FOLDER + "\\" + filepath

    return pd.read_excel(filepath) if filepath.endswith(".xlsx") else pd.read_csv(filepath)

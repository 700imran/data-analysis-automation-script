import os
import pandas as pd
from datetime import datetime

OUTPUT_FOLDER = r"C:\Users\Dell\Documents\Data Analysis Output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def save_output(df, filepath, analysis_type):
    """
    Always saves a fixed live dashboard file.
    Optionally saves a separate timestamped file if user wants.
    """

    # Extract input file name
    input_name = os.path.splitext(os.path.basename(filepath))[0]

    # Build filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    archive_filename = f"{input_name}_{analysis_type}_output_{timestamp}.csv"
    fixed_filename = f"{input_name}_{analysis_type}_output.csv"

    # ✅ Always save fixed live dashboard file (no question asked)
    df.to_csv(os.path.join(OUTPUT_FOLDER, fixed_filename), index=False)
    print(f"✅ Updated live dashboard file: {fixed_filename}")

    # ✅ Ask only if user wants a separate archive file
    choice = input(
        "\nDo you want to save a separate timestamped file?\n"
        "1 = Yes (create archive file)\n"
        "2 = No (only update live dashboard)\n"
        "Enter choice: "
    ).strip()

    if choice == "1":
        df.to_csv(os.path.join(OUTPUT_FOLDER, archive_filename), index=False)
        print(f"✅ Saved archive file: {archive_filename}")

    elif choice == "2":
        print("✅ No archive file created.")

    else:
        print("⚠️ Invalid choice. Only live dashboard file saved.")

import glob
import os
from datetime import datetime
import pandas as pd
from config import RAW_DATA_DIR, LOG_DIR


def load_raw_data_files(raw_data_dir=RAW_DATA_DIR, log_dir=LOG_DIR, verbose=True):
    """
    Loads all supported raw data files (CSV, Excel) into a list of DataFrames.

    :param RAW_DATA_DIR: Path to the directory containing raw data files.
    :param verbose: Whether to print status messages.
    :return: List of loaded DataFrames
    """
    dfs = []
    files_loaded = []
    log_lines = []

    file_patterns = ["*.csv", "*.xlsx"]
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(os.path.join(raw_data_dir, pattern)))

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'delay_load_log_{timestamp}.txt'
    log_path = os.path.join(log_dir, log_filename)


    for file_path in all_files:
        if os.path.exists(file_path):
            try:
                if file_path.endswith(".xlsx"):
                    df = pd.read_excel(file_path)
                else: # csv files
                    df = pd.read_csv(file_path)

                dfs.append(df)
                files_loaded.append(file_path)
                log_lines.append(f"Loaded {file_path} successfully")

                if verbose:
                    print(f"Loaded: {file_path}")

            except Exception as e:
                log_lines.append(f"Error loading {file_path}: {e}")
                if verbose:
                    print(f"Error loading {file_path}: {e}")

            summary = f"Loaded {len(files_loaded)} out of {len(all_files)} files."
            log_lines.append(summary)
            if verbose:
                print(summary)

    with open(log_path, "w", encoding="utf-8") as f:
        for line in log_lines:
            f.write(line + "\n")

    return dfs

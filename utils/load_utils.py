import glob
import os
from datetime import datetime
import pandas as pd
from config import DELAY_DATA_DIR , LOG_DIR
from utils import log_utils


def load_raw_data_files(delay_data_dir:str=DELAY_DATA_DIR , log_dir:str=LOG_DIR, verbose=True) \
        -> tuple[list[pd.DataFrame], list[str]]:
    """
    Load all supported raw data files (Excel) from a directory.

    :param delay_data_dir: Directory containing the raw data files.
    :param log_dir: Directory where logs should be written.
    :param verbose: If True, print status messages while loading.
    :return: list of pd.Dataframes containing loaded DataFrames and list of corresponding filenames filename
    """

    dfs = []
    files_loaded = []
    log_lines = []

    file_patterns = ["*.xlsx"]
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(os.path.join(delay_data_dir, pattern)))

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename_prefix = f'delay_load_log_{timestamp}.txt'


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

    log_utils.write_log(log_lines, log_filename_prefix, log_dir)


    return dfs, files_loaded

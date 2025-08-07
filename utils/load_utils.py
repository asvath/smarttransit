import glob
import os

import pandas as pd

from config import RAW_DELAY_DIR, LOG_DIR
from utils import log_utils


def load_raw_data_files(raw_delay_dir:str=RAW_DELAY_DIR , log_dir:str=LOG_DIR, verbose=True) \
        -> tuple[list[pd.DataFrame], list[str]]:
    """
    Load all supported raw data files (Excel).

    :param raw_delay_dir: Directory containing the raw data files.
    :param log_dir: Directory where logs should be written.
    :param verbose: If True, print status messages while loading.
    :return: list of pd.Dataframes containing loaded DataFrames and list of corresponding filenames
    """

    dfs = []
    files_loaded = []
    log_lines = []

    file_patterns = ["*.xlsx"]
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(os.path.join(raw_delay_dir, pattern)))

    log_filename_prefix = f'raw_delay_load_log'

    for file_path in all_files:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, dtype={'Date': 'string', 'Time': 'string'})
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

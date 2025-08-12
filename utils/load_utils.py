import glob
import os
from typing import Dict, List

import pandas as pd

from config import RAW_DELAY_DIR, LOG_DIR
from utils import log_utils


def load_raw_data_files(raw_delay_dir:str=RAW_DELAY_DIR , log_dir:str=LOG_DIR, verbose=True) \
        ->  Dict[str, List[pd.DataFrame]]:
    """
    Load all supported raw data files (Excel) and read *all* sheets.

    :param raw_delay_dir: Directory containing the raw data files.
    :param log_dir: Directory where logs should be written.
    :param verbose: If True, print status messages while loading.
    :return: dict mapping file path to list of DataFrames (one per sheet).
    """

    log_lines = []
    file_to_sheets= {} # dict mapping file path to list of dataframes (one per sheet).

    file_patterns = ["*.xlsx"]
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(os.path.join(raw_delay_dir, pattern)))
    all_files = sorted(all_files)

    # if no datafiles
    if not all_files:
        msg = f"No files found in {raw_delay_dir} matching {file_patterns}."
        log_lines.append(msg)
        if verbose:
            print(msg)
        log_utils.write_log(log_lines, "raw_delay_load_log", log_dir)
        return file_to_sheets

    for file_path in all_files:
            try:
                # Read *all* sheets into a dict
                i = 0
                sheets_dict = pd.read_excel(file_path, sheet_name=None)
                # the sheets either have 1 sheet or 12 sheets, one for each month
                n = len(sheets_dict)
                if n not in (1,12):
                    msg = f"Skipping {file_path}: expected 1 or 12 sheets, found {n}."
                    log_lines.append(msg)
                    if verbose:
                        print(msg)
                    continue

                file_to_sheets[file_path] = []
                for _, sheet_df in sheets_dict.items():
                    file_to_sheets[file_path].append(sheet_df)

                log_lines.append(f"Loaded {file_path} successfully with {len(file_to_sheets[file_path])} out "
                                 f"{sheets_dict.items()} sheet(s)")

                if verbose:
                    print(f"Loaded: {file_path}")

            except Exception as e:
                msg = f"Error loading {file_path}: {e}"
                log_lines.append(msg)
                if verbose:
                    print(msg)

            summary = f"Loaded {len(file_to_sheets)} out of {len(all_files)} files."
            log_lines.append(summary)
            if verbose:
                print(summary)

    log_utils.write_log(log_lines, "raw_delay_load_log", log_dir)

    return file_to_sheets
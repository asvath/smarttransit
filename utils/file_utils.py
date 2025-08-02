import os
from datetime import datetime

import pandas as pd

"""
Utility functions for writing and saving various data outputs (e.g CSV) during TTC delay data preprocessing.
"""
def write_to_csv(df:pd.DataFrame, prefix: str, output_dir:str) -> str:
    """
    Saves a DataFrame to a CSV file with a timestamped filename.

    :param df: The DataFrame to save.
    :param prefix: The prefix for the filename
    :param output_dir: The directory where the file will be saved.
    :return: The full path to the saved CSV file.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(output_dir, f'{prefix}_{timestamp}.csv')
    df.to_csv(path, index=False)
    return path
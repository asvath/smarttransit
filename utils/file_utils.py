import os
from datetime import datetime

import pandas as pd

"""
Utility functions for writing and saving various data outputs (e.g CSV) during TTC delay data preprocessing.
"""
def write_to_csv(df:pd.DataFrame, prefix: str, output_dir:str, timestamped = True) -> str:
    """
    Saves a DataFrame to a CSV file with a timestamped filename.

    :param df: The DataFrame to save.
    :param prefix: The prefix for the filename
    :param output_dir: The directory where the file will be saved.
    :return: The full path to the saved CSV file.
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    date_folder = os.path.join(output_dir, date_str)
    os.makedirs(date_folder, exist_ok=True)  # Create folder if it doesn't exist

    if timestamped:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(date_folder, f'{prefix}_{timestamp}.csv')
    else:
        path = os.path.join(date_folder, f'{prefix}.csv')
    df.to_csv(path, index=False)
    return path

def read_csv(filepath: str) -> pd.DataFrame:
    """
     Reads csv as pandas DataFrame.
    :param filepath: Path to csv
    :return: pd.DataFrame
    """

    return pd.read_csv(filepath)

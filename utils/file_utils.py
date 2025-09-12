import os
from datetime import datetime
import json

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

def read_txt_to_list(filepath:str) -> list:
    """
    Reads a txt as a list
    :param filepath: Path to txt
    :return: list
    """

    # Open a text file and read lines into a list
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove newline characters, keeps line if not empty
    lines = [line.strip() for line in lines if line.strip()]

    return lines

def write_to_json(filepath:str, data:list|dict) -> str:
    """
    Writes data into a json file
    :param filepath: Path to data
    :param data: list containing data dictionaries
    :return: filepath name
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return filepath
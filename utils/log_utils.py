import os
from datetime import datetime

import pandas as pd

from config import LOG_DIR
"""
Utility functions for logging various outputs during TTC delay data preprocessing.

Includes:
- Logging unique stations by category (passenger, non-passenger, unknown)
- Logging station names with directional phrases (to, toward, towards)
"""

def write_log(log_lines:list, prefix: str, log_dir = LOG_DIR) -> str:
    """
    Writes log and saves to disk
    :param log_lines: list of log lines
    :param prefix: prefix of log file name
    :param log_dir: log directory
    :return: log_path: absolute path of log
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    date_folder = os.path.join(log_dir, date_str)
    os.makedirs(date_folder, exist_ok=True)  # Create folder if it doesn't exist

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_path = os.path.join(date_folder, f'{prefix}_{timestamp}.txt')
    with open(log_path, 'w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')
    return log_path

def log_unique_stations_by_category(df:pd.DataFrame, log_dir:str = LOG_DIR) -> None:
    """
    Logs unique station names by each category into separate text files.
    :param df: pd.DataFrame
    :param log_dir: log directory
    :return:None
    """

    for category in ['Passenger', 'Non-passenger', 'Unknown']:
        stations_in_category = df[df['Station Category'] == category]['Station'].unique()
        stations_in_category.sort()
        log_lines = list(stations_in_category)
        prefix = f'stations_{category.lower()}'
        log_path = write_log(log_lines, prefix, log_dir)
        print(f"Logged stations in {category} category to {log_path}")

def log_station_names_with_directionals(df:pd.DataFrame, log_dir :str = LOG_DIR) -> None:
    """
    Logs station names with directionals into log file.
    :param df: pd.Dataframe
    :param log_dir : log directory
    :return: None
    """

    mask = df['Station'].str.contains(r'\b(to|toward|towards)\b', case=False, na=False)
    stations_with_directions = df[mask]
    stations_with_directions = stations_with_directions['Station'].unique()
    stations_with_directions.sort()

    log_lines = list(stations_with_directions)
    prefix = "station_spans_with_to_towardx"
    log_path = write_log(log_lines, prefix, log_dir)
    print(f"Logged {len(stations_with_directions)} station names with directionals to {log_path}")

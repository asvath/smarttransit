import ast
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

from config import (CODE_DESC_DIR, VALID_STATIONS_WITH_LINECODES, CODE_DESCRIPTIONS, LOG_DIR,
                    REFERENCE_COLS_ORDERED, VALID_BOUND_NAMES)


def merge_delay_data(dfs: list[pd.DataFrame],files_loaded: list, log_dir=LOG_DIR,
                           reference_cols_ordered: list[str]= REFERENCE_COLS_ORDERED, verbose: bool = True):
    """
    Validates and merges delay dataframes.
    :param files_loaded: list of the name of the dataframe files
    :param dfs: List of raw pandas DataFrames to merge.
    :param reference_cols_ordered: Expected column names in the desired order.
    :param log_dir: Path to a log directory.
    :param verbose: Whether to print status messages during processing.
    :return: pd.DataFrame: A single cleaned, merged dataframe.
    """

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'delay_merge_log_{timestamp}.txt'
    log_path = os.path.join(log_dir, log_filename)

    reference_cols_set = set(reference_cols_ordered)
    log_lines = []
    valid_dfs = [] # store df that have no missing or extra columns (apart from ID) and are good to merge
    valid_filenames = []  # filename of the valid dfs

    for i, df in enumerate(dfs):
        current_cols = set(df.columns)
        missing = reference_cols_set - current_cols
        extra = current_cols - reference_cols_set
        if missing or (extra and extra != {'_id'}):
            log_lines.append(f"File {files_loaded[i]} has issues:")
            if missing:
                log_lines.append(f"   Missing columns: {sorted(missing)}")
                log_lines.append("   -> Skipping due to missing columns.\n")
            elif extra:
                log_lines.append(f"   Extra columns: {sorted(extra)}")
                log_lines.append("   -> Skipping due to unknown extra columns.\n")
            continue

        if '_id' in extra:
            log_lines.append(f"File {files_loaded[i]} has '_id' column.")
            log_lines.append("   -> Dropping '_id' column.")
            df = df.drop(columns=['_id'])

        # All good, or cleaned — reindex and add to valid list
        df = df.reindex(columns=reference_cols_ordered)
        valid_dfs.append(df)
        valid_filenames.append(files_loaded[i])

    if valid_dfs:
        combined_df = pd.concat(valid_dfs, ignore_index=True)

        if verbose:
            print("Merged DataFrame shape:", combined_df.shape)
            print("Preview:")
            print(combined_df.head())

        log_lines.append(f"Merged {len(valid_dfs)} out of {len(dfs)} files.")
        log_lines.append("Files merged:")
        for filename in valid_filenames:
            log_lines.append(f" - {filename}")

    else:
        combined_df = pd.DataFrame()
        log_lines.append("No valid files were merged.")

    with open(log_path, 'w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')

    return combined_df

def drop_invalid_rows(df):
    """
    Drops rows with missing values, no recorded delay, or missing vehicle numbers.

    This ensures only meaningful delay events are kept for analysis.

    :param df: pandas DataFrame with 'Min Delay' and 'Vehicle' columns
    :return: Cleaned pandas DataFrame
    """
    df = df.dropna()
    df = df[df['Min Delay'] != 0]
    df = df[df['Vehicle'] != 0]
    return df

def clean_station_name(name:str) -> str:
    """
    clean and standardize the TTC station name, e.g UNION STATION TOWARD K, becomes UNION STATION
    :param name: name of the TTC station
    :return: clean name of the TTC station
    """

    name = str(name).strip().upper() # strips leading and trailing white spaces, makes everything upper case
    name = re.sub(r'\s+', ' ', name) # replaces any spaces that are one or more tabs in the name to one

    # Normalize 'St' to 'St.'
    name = re.sub(r'\bST\b(?=\s)', 'ST.', name)

    # Remove embedded line codes (YUS, BD, L1, L2, etc.) from anywhere in the name
    name = re.sub(r'\b(YU|YUS|BD|BDL|BDN|BD-S|L1|L2|LINE\s?\d+)\b', '', name)

    # clean up extra whitespace left behind
    name = re.sub(r'\s+', ' ', name)


    # Fix endings like "STATIO", "STA", etc.
    name = name.strip() # remove white spaces in the beginning and the end
    if name.endswith(" STATIO") or name.endswith(" STA"):
        name = re.sub(r'( STATIO| STA)$', ' STATION', name)


    legit_station_endname_keywords = ['STATION', 'YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
    if name.split(' ')[-1] not in legit_station_endname_keywords:
        name += ' STATION'


    # Fixes abbreviations and Dual Named Interchange Stations
    station_map = {
        'VMC STATION': 'VAUGHAN METROPOLITAN CENTRE STATION',
        'VAUGHAN MC STATION': 'VAUGHAN METROPOLITAN CENTRE STATION',
        'NORTH YORK CTR STATION': 'NORTH YORK CENTRE STATION',
        'BLOOR STATION': 'BLOOR-YONGE STATION',
        'BLOOR/YONGE STATION': 'BLOOR-YONGE STATION',
        'YONGE STATION': 'BLOOR-YONGE STATION',
        'YONGE-UNIVERSITY AND B': 'BLOOR-YONGE STATION',
        'SHEPPARDYONGE STATION': 'SHEPPARD-YONGE STATION',
        'SHEPPARD STATION': 'SHEPPARD-YONGE STATION',
        'YONGE SHEP STATION': 'SHEPPARD-YONGE STATION',
        'YONGE SHP STATION': 'SHEPPARD-YONGE STATION',
        'SHEPPARD YONGE STATION': 'SHEPPARD-YONGE STATION'}

    key = name.strip().upper()
    if key in station_map:
        name = station_map[key]

    # clean up extra whitespace left behind
    name = re.sub(r'\s+', ' ', name)
    # Fix spelling error for Station

    return name

def clean_station_column(df):
    """
    Applies `clean_station_name` function to the 'Station' column in the DataFrame.
    """
    df['Station'] = df['Station'].apply(clean_station_name)
    return df

def categorzie_station(name:str) -> str:
    """
    This function checks if a station is a valid passenger station, non-passenger (e.g YARD, WYE etc),
    or unknown (e.g SRT stations, approaching Rosedale, spelling error).
    :param name: cleaned str of the station name
    :return: str indicating passenger, non-passenger or unknown
    """

    valid_station_linecode = valid_station_linecode_dict()

    non_passenger_endname_keywords = ['YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
    if name in valid_station_linecode.keys():
        category = "passenger"
    elif name.split(' ')[-1] in non_passenger_endname_keywords:
        category = "non-passenger"
    else:
        category = "unknown" #e.g approaching Rosedale
    return category

def add_station_category(df):
    df['Station Category'] = df['Station'].apply(categorzie_station)
    return df


def valid_station_linecode_dict() -> dict:
    """
    Creates dictionary with valid in operation stations and their respective linecodes
    :return: dict
    """
    valid_station_linecode = {}
    with open(VALID_STATIONS_WITH_LINECODES) as f:
        for line in f:
            if line.strip(): # non-empty
                name, linecode = line.upper().split("STATION")
                valid_station_linecode[name + "STATION"] = ast.literal_eval(linecode.strip())
    return valid_station_linecode

def clean_linecode(df):
    """
    This function will fix incorrect linecodes using the valid_station_linecode_dict.
    :param df: pd.Dataframe
    :return: pd.Dataframe
    """
    valid_station_linecode = valid_station_linecode_dict()

    for index, row in df.iterrows():
        station = row["Station"]
        line = row["Line"]

        if station not in valid_station_linecode: # a non-passenger station or unknown
            continue

        valid_codes = valid_station_linecode[station]

        if line in valid_codes:
            continue # already the correct code

        if len(valid_codes) > 1: # Too ambiguous to fix. e.g. Bloor-Yonge subway,
            # if the linecode is not BD or YU, we wouldn't know which is the correct code
            df.at[index, "Line"] = np.nan


        else: # fix to the correct code
            df.at[index, "Line"] = valid_codes[0]  # Fix to the correct code

    return df

def clean_and_add_datetime(df):
    """
    Cleans and standardizes the 'Date' and 'Time' columns as pandas datetime objects,
    and creates a combined 'DateTime' column for full timestamp analysis.
    This prepares the data for time-based operations such as extracting hour, weekday, or performing time filtering.

    :param df: pandas DataFrame with 'Date' and 'Time' columns as strings
    :return: pandas DataFrame with added 'DateTime' column
    """

    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    return df

def clean_day(df):
    """
     Extracts the day of the week from the 'Date' column and stores it in a 'Day' column. This will fix any errors
     in the 'Day' column.

    :param df: pandas DataFrame with a 'Date' column as datetime.date
    :return: pandas DataFrame with added or updated 'Day' column
    """
    df['Day'] = df['Date'].dt.day_name()
    return df

def add_IsWeekday(df):
    """
    Adds a new column 'IsWeekday' to indicate whether each date falls on a weekday.
    :param df:
    :return:
    """
    df['IsWeekday'] = df['Date'].dt.weekday < 5  # True for weekdays, False for weekends
    return df

def clean_bound(df):

    df.loc[~df['Bound'].isin(VALID_BOUND_NAMES), 'Bound'] = np.nan

    return df

def clean_delay_code_descriptions():
    """
    Loads a CSV file containing TTC delay code descriptions, removes all non-ASCII characters
    from the text fields, and saves a cleaned version to disk.

    This helps ensure the output file is encoding-safe and free of mojibake characters like â or Ã.

    The cleaned file is saved to:
    'data/raw/code_descriptions/Clean Code Descriptions.csv'

    :return: None
    """
    codes = pd.read_csv(CODE_DESCRIPTIONS, encoding='utf-8-sig')

    def remove_non_ascii(text):
        return re.sub(r'[^\x00-\x7F]+', '', text) if isinstance(text, str) else text

    codes_cleaned = codes.applymap(remove_non_ascii)
    filepath = os.path.join(CODE_DESC_DIR,"Clean Code Descriptions.csv")
    codes_cleaned.to_csv (filepath,index=False, encoding='utf-8-sig')

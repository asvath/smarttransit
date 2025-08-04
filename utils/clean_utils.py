import ast
import os
import re
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd
from utils import log_utils, file_utils

from config import (CODE_DESC_DIR, VALID_STATIONS_WITH_LINECODES, CODE_DESCRIPTIONS, LOG_DIR,
                    REFERENCE_COLS_ORDERED, VALID_BOUND_NAMES, DROPPED_RAW_DATA_DIR, WEEKDAY_RUSH_HOUR, SEASONS,
                    VALID_BOUND_NAMES_W_LINECODES)


def merge_delay_data(dfs: list[pd.DataFrame],files_loaded: list, log_dir=LOG_DIR,
                           reference_cols_ordered: list[str]= REFERENCE_COLS_ORDERED, verbose: bool = True):
    """
    Standardizes and merges multiple raw delay DataFrames into a single DataFrame.

    This function:
    - Logs missing or extra columns
    - Skips DataFrames with missing columns or unexpected extra columns (excluding, '_id')
    - Drops unnecessary  '_id' column if present.
    - Reorders columns to match a reference schema.
    - Merges valid DataFrames into one.

    :param dfs: List of raw pandas DataFrames to be merged.
    :param files_loaded: List of filenames corresponding to the DataFrames (used for logging).
    :param reference_cols_ordered: List of expected column names in the desired order.
    :param log_dir: Directory where logs should be saved.
    :param verbose: Whether to print merging status and preview of the merged DataFrame.
    :return: A single merged pandas DataFrame with standardized columns. Empty if no valid files were found.
    """

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename_prefix = f'delay_merge_log_{timestamp}'


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

    log_utils.write_log(log_lines, log_filename_prefix, log_dir)


    return combined_df

def drop_invalid_rows(df: pd.DataFrame, dropped_raw_data_dir: str = DROPPED_RAW_DATA_DIR):
    """
    Drops rows with missing values, no recorded delay, no gaps, or missing vehicle numbers.

    This ensures only meaningful delay events are kept for analysis.

    :param df: Raw pd.DataFrame
    :param dropped_raw_data_dir: Directory to store dropped data
    :return: pd.DataFrame with invalid rows removed
    """

    drop_conditions = {}

    # Drop rows with missing values
    drop_conditions["missing_values"] = df[df.isnull().any(axis=1)]
    df = df.dropna()

    # Drop rows where delay is zero
    drop_conditions["zero_min_delay"] = df[df['Min Delay'] == 0]
    df = df[df['Min Delay'] != 0]

    # Drop rows where gap is zero
    drop_conditions["zero_gap"] = df[df['Min Gap'] == 0]
    df = df[df['Min Gap'] != 0]

    # Drop rows where delay is < than gap:
    drop_conditions["delay_less_than_gap"] = df[df['Min Delay'] >= df['Min Gap']]
    df = df[df['Min Delay'] < df['Min Gap']]

    # Drop rows where vehicle is zero
    drop_conditions["zero_vehicle_number"] = df[df['Vehicle'] == 0]
    df = df[df['Vehicle'] != 0]

    # Write out dropped data
    for condition, dropped_df in drop_conditions.items():
        if not dropped_df.empty:
            file_utils.write_to_csv(df=dropped_df, prefix=condition, output_dir=dropped_raw_data_dir)

    return df

def clean_station_name(name:str) -> str:
    """
    Clean and standardize a TTC station name by:
    - Normalizing 'St' to 'St.' (e.g., 'St George' to 'St. George')
    - Removing embedded line codes from the name (e.g., 'YUS', 'BD', 'L1', etc.)
    - Correcting misspellings of 'Station'
    - Adding 'Station' to names that do not end with a legitimate station-type keyword
    - Standardizing abbreviations and dual-named interchange stations
    :param name: Raw name of the TTC station
    :return: Cleaned and standardized TTC station name
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

def clean_station_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans station names in 'Station' columns by applying `clean_station_name` function
    :param df: pd.Dataframe
    :return pd.Dataframe with cleaned station names
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

def add_station_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Station Category' column to the DataFrame, labeling each station as
    'passenger', 'non-passenger', or 'unknown'.
    :param df: pd.Dataframe
    :return: pd.Dataframe with added 'Station Category' column
    """
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

def clean_linecode(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fixes incorrect linecodes using the valid_station_linecode_dict.
    :param df: pd.Dataframe
    :return: pd.Dataframe with clean linecode
    """
    valid_station_linecode = valid_station_linecode_dict()

    for index, row in df.iterrows():
        station = row["Station"]
        line = row["Line"]

        if station not in valid_station_linecode: # a non-passenger station or unknown
            continue

        # valid codes for the station
        valid_codes = valid_station_linecode[station]

        if line in valid_codes:
            continue # already the correct code

        if len(valid_codes) > 1: # Too ambiguous to fix. e.g. Bloor-Yonge subway,
            # if the linecode is not BD or YU, we wouldn't know which is the correct code
            df.at[index, "Line"] = np.nan


        else: # fix to the correct code
            df.at[index, "Line"] = valid_codes[0]  # Fix to the correct code

    return df

def clean_and_add_datetime(df: pd.DataFrame):
    """
    Cleans and standardizes the 'Date' and 'Time' columns as strings,
    and creates a combined 'DateTime' column  as pandas datetime objects for full timestamp analysis.
    This prepares the data for time-based operations such as extracting hour, weekday, or performing time filtering.

    :param df: pd.DataFrame with 'Date' and 'Time' columns as standardized strings
    :return: pd.DataFrame with added 'DateTime' column as standardized pandas datetime objects
    """
    df.columns = df.columns.str.strip()
    df = clean_date(df)
    df = clean_time(df)

    # Combine date and time into one string (e.g., "2025-01-01 08:15:00")
    base = df['Date'] + ' ' + df['Time']

    # Create 'DateTime' column with YYYY-MM-DD HH:MM:SS format as a pandas datetime object
    df['DateTime'] = pd.to_datetime(base, format='%Y-%m-%d %H:%M:%S', errors='coerce')

    return df

def clean_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the 'Date' column in raw TTC Excel delay data.

    - Reads 'Date' column as strings and parses various common formats such as DD/MM/YYYY,
    YYYY-MM-DD, and M/D/YYYY.
    - Converts all entries to a consistent string format: 'YYYY-MM-DD'.

    :param df: pd.DataFrame containing a 'Date' column as strings
    :return: pd.DataFrame with 'Date' column as standardized 'YYYY-MM-DD' strings
    """

    # Date is already a string, normalize whitespace
    d = df['Date'].astype('string').str.strip()

    # Parse Dates
    # Try dayfirst=True first (for DD/MM/YYYY), then year first or month first
    d1 = pd.to_datetime(d, errors='coerce', dayfirst=True)
    d2 = pd.to_datetime(d, errors='coerce')  # standard inference (YYYY-MM-DD, M/D/YYYY)
    # if d1 is NaT then fill up with d2
    d_parsed = d1.fillna(d2)

    # Standardize to YYYY-MM-DD string format
    df['Date'] = d_parsed.dt.strftime('%Y-%m-%d')

    return df

def clean_time(df: pd.DataFrame):
    """
    Cleans and standardizes the 'Time' column in a DataFrame.

    - Handles times in both HH:MM and HH:MM:SS formats.
    - Strips extra whitespace.
    - Converts valid times to consistent 'H:M:S' string format (e.g.'8:15:00')

    :param df: pd.DataFrame
    :return: pd.DataFrame with cleaned 'Time' column as string in H:M:S format
    """

    # Time is already a string, normalize whitespace
    t = df['Time'].astype('string').str.strip()

    # Parsing rows with HH:MM format
    t_hm = pd.to_datetime(t, format='%H:%M', errors='coerce')

    # Parsing rows with HH:MM:SS format
    t_hms = pd.to_datetime(t, format='%H:%M:%S', errors='coerce')

    # If t_hm is NaT then fill up with t_hms
    parsed_time = t_hm.fillna(t_hms)

    # Standardize time to HH:MM:SS string format
    df['Time'] = parsed_time.dt.strftime('%H:%M:%S')

    return df

def clean_day(df: pd.DataFrame):
    """
     Extracts the day of the week from the 'Date' column and stores it in a 'Day' column. This will fix any errors
     in the 'Day' column.

    :param df: pandas DataFrame with a 'Date' column as datetime.date
    :return: pandas DataFrame with updated 'Day' column
    """
    df['Day'] = df['DateTime'].dt.day_name()
    return df

def add_IsWeekday(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a new column 'IsWeekday' to indicate whether each date falls on a weekday.
    :param df: pd.Dataframe with Datetime column
    :return: pd.Dataframe with added 'IsWeekday' column
    """
    df['IsWeekday'] = df['DateTime'].dt.weekday < 5  # True for weekdays, False for weekends
    return df

# def clean_bound(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Clean bound names, if bound names are not 'N, S, E, W', set to Nan. Check bound names against line codes.
#     :param df: pd.Dataframe
#     :return: pd.Dataframe with clean bound names
#     """
#     df.loc[~df['Bound'].isin(VALID_BOUND_NAMES_W_LINECODES), 'Bound'] = np.nan
#     for index, row in df.iterrows():
#         line = row["Line"]
#         bound = row["Bound"]
#         if line in VALID_BOUND_NAMES_W_LINECODES:
#             if bound not in VALID_BOUND_NAMES_W_LINECODES[line]:
#                 row["Bound"] = np.nan
#
#
#     return df

def categorize_rush_hour(row:  pd.Series, weekday_rush_hour:dict= WEEKDAY_RUSH_HOUR) -> str:
    """
    Categorizes rush hour into morning, afternoon, offpeak or weekend

    :param row: row from pd.DataFrame
    :param weekday_rush_hour: Dictionary with keys for start/end times of rush hours.
    :return: Rush hour category
    """

    if row['IsWeekday'] == True:
        t = row['DateTime'].time()
        if  weekday_rush_hour["morning start"]  <= t <= weekday_rush_hour["morning end"]:
            return "morning"
        elif weekday_rush_hour["evening start"]  <= t <= weekday_rush_hour["evening end"]:
            return "evening"
        else:
            return "off peak"

    else:
        return "weekend"

def add_rush_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Rush Hour' column to the DataFrame, categorizing each row as
    'morning', 'evening', 'off peak', or 'weekend' based on the time and day.

    :param df: pd.DataFrame
    :return: df: pd.DataFrame with an added 'Rush Hour' column
    """
    df['Rush Hour'] =  df.apply(categorize_rush_hour, axis =1)
    return df

def get_season(dt: pd.Timestamp, seasons: Dict[str, List[int]] = SEASONS) -> str:
    """
    Determines season for a given timestamp
    :param dt: DateTime row
    :param seasons: Dictionary mapping season names to lists of month numbers
    :return: season
    """
    month = dt.month
    for season, months in seasons.items():
        if month in months:
            return season

    return "Unknown"

def add_season(df:pd.DataFrame) -> pd.DataFrame:
    """
    Adds "Season" column
    :param df: pd.DataFrame with "DateTime" column
    :return: pd.DataFrame with added "Season" column
    """
    df["Season"] = df["DateTime"].apply(get_season)
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

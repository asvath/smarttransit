import ast
import os
import re
from sys import prefix
from typing import Dict, List

import numpy as np
import pandas as pd

from config import (RAW_CODE_DESC_DIR, VALID_STATIONS_W_LINECODES_FILE, CODE_DESCRIPTIONS_FILE, LOG_DIR,
                    REFERENCE_COLS_ORDERED, DROPPED_RAW_DATA_DIR, WEEKDAY_RUSH_HOUR_DICT, SEASONS_TO_MONTHS_DICT,
                    VALID_LINECODES_TO_BOUND_DICT, PROCESSED_CODE_DESCRIPTIONS_FILE, NAME_CHANGES)
from utils import log_utils, file_utils


def merge_delay_data(file_to_sheets:dict[str, list], log_dir=LOG_DIR,
                           reference_cols_ordered: list[str]= REFERENCE_COLS_ORDERED, verbose: bool = True):
    """
    Standardizes and merges multiple raw delay DataFrames into a single DataFrame.

    This function:
    - Logs missing or extra columns
    - Skips DataFrames with missing columns or unexpected extra columns (excluding, '_id')
    - Drops unnecessary  '_id' column if present.
    - Reorders columns to match a reference schema.
    - Merges valid DataFrames into one.

    :param file_to_sheets: Dict of filenames and corresponding list of raw pandas DataFrames to be merged.
    :param reference_cols_ordered: List of expected column names in the desired order.
    :param log_dir: Directory where logs should be saved.
    :param verbose: Whether to print merging status and preview of the merged DataFrame.
    :return: A single merged pandas DataFrame with standardized columns. Empty if no valid files were found.
    """

    log_filename_prefix = f'raw_delay_merge_log'


    reference_cols_set = set(reference_cols_ordered)
    log_lines = []
    valid_dfs = [] # store df that have no missing or extra columns (apart from ID) and are good to merge
    merged_files = []  # names of files that have been merged

    for file, dfs in file_to_sheets.items():
        # iterate through each sheet
        merged_sheet_count = 0

        for i, df in enumerate(dfs):
            current_cols = set(df.columns)
            missing = reference_cols_set - current_cols
            extra = current_cols - reference_cols_set
            if missing or (extra and extra != {'_id'}):
                log_lines.append(f"File {file}, sheet {i} has issues:")
                if missing:
                    log_lines.append(f"   Missing columns: {sorted(missing)}")
                    log_lines.append("   -> Skipping due to missing columns.\n")
                elif extra:
                    log_lines.append(f"   Extra columns: {sorted(extra)}")
                    log_lines.append("   -> Skipping due to unknown extra columns.\n")
                continue

            if '_id' in extra:
                log_lines.append(f"File {file}, sheet {i} has '_id' column.")
                log_lines.append("   -> Dropping '_id' column.")
                df = df.drop(columns=['_id'])

            # All good, or cleaned — reindex and add to valid list
            df = df.reindex(columns=reference_cols_ordered)
            valid_dfs.append(df)
            merged_sheet_count += 1

        if merged_sheet_count:
            merged_files.append(file)
            log_lines.append(f"Merged {merged_sheet_count} of {len(dfs)} sheet(s) from {file}.")
        else:
            log_lines.append(f"No valid sheets merged from {file}.")

    if valid_dfs:
        combined_df = pd.concat(valid_dfs, ignore_index=True)

        if verbose:
            print("Merged DataFrame shape:", combined_df.shape)
            print("Preview:")
            print(combined_df.head())

        log_lines.append(f"Merged {len(merged_files)} of {len(file_to_sheets)} files.")

    else:
        combined_df = pd.DataFrame()
        log_lines.append("No valid files were merged.")

    log_utils.write_log(log_lines, log_filename_prefix, log_dir)


    return combined_df

def drop_duplicates(df:pd.DataFrame, dropped_raw_data_dir = DROPPED_RAW_DATA_DIR) -> pd.DataFrame:
    """
    Drops duplicate rows
    :param df: Raw pd.DataFrame
    :param dropped_raw_data_dir: Directory to store dropped data
    :return pd.DataFrame with duplicates dropped
    """
    duplicates = df[df.duplicated(keep=False)]
    prefix = "duplicates"
    print(f"Rows dropped: duplicates saved in {dropped_raw_data_dir}")
    file_utils.write_to_csv(df=duplicates, prefix=prefix, output_dir=dropped_raw_data_dir)

    return df.drop_duplicates(keep="first")

def drop_invalid_rows(df: pd.DataFrame, dropped_raw_data_dir: str = DROPPED_RAW_DATA_DIR):
    """
    Drops rows with missing values, no recorded delay, no time gaps between delayed train and prior train,
    recorded delay less than time gap between delayed train and prior train, or missing vehicle numbers.

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

    # Drop rows where the delay is more than the time gap between delayed train and the train ahead
    drop_conditions["delay_more_than_gap"] = df[df['Min Delay'] >= df['Min Gap']]
    df = df[df['Min Delay'] < df['Min Gap']]

    # Drop rows where vehicle is zero
    drop_conditions["zero_vehicle_number"] = df[df['Vehicle'] == 0]
    df = df[df['Vehicle'] != 0]

    # Write out dropped data
    for condition, dropped_df in drop_conditions.items():
        if not dropped_df.empty:
            file_utils.write_to_csv(df=dropped_df, prefix=condition, output_dir=dropped_raw_data_dir)
            print(f"Rows dropped: {condition} saved in {dropped_raw_data_dir}")
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
    name = name.strip()
    name = re.sub(r'( STATIO| STA| STN| STAION)$', ' STATION', name)

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
        'YONGE AND BLOOR STATION': 'BLOOR-YONGE STATION',
        'YONGE-BLOOR STATION': 'BLOOR-YONGE STATION',
        'YONGE STATION': 'BLOOR-YONGE STATION',
        'YONGE-UNIVERSITY AND B': 'BLOOR-YONGE STATION',
        'SHEPPARDYONGE STATION': 'SHEPPARD-YONGE STATION',
        'SHEPPARD STATION': 'SHEPPARD-YONGE STATION',
        "YONGE SHEPPARD" : 'SHEPPARD-YONGE STATION',
        'YONGE SHEP STATION': 'SHEPPARD-YONGE STATION',
        'YONGE SHP STATION': 'SHEPPARD-YONGE STATION',
        'SHEPPARD YONGE STATION': 'SHEPPARD-YONGE STATION'}

    key = name.strip().upper()
    if key in station_map:
        name = station_map[key]

    # clean up extra whitespace left behind
    name = re.sub(r'\s+', ' ', name)

    return name

def clean_station_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans station names in 'Station' columns by applying `clean_station_name` function
    :param df: pd.Dataframe
    :return pd.Dataframe with cleaned station names
    """
    df['Station'] = df['Station'].apply(clean_station_name)
    return df

def valid_station_linecode_dict() -> dict:
    """
    Creates dictionary with valid in operation stations and their respective linecodes, e.g {"ROSEDALE STATION": "YU"}
    :return: dict
    """
    valid_station_linecode = {}
    with open(VALID_STATIONS_W_LINECODES_FILE) as f:
        for line in f:
            if line.strip(): # non-empty
                name, linecode = line.upper().split("STATION")
                valid_station_linecode[name + "STATION"] = ast.literal_eval(linecode.strip())
    return valid_station_linecode

def categorize_station(name:str, valid_station_linecode:dict) -> str:
    """
    This function checks if a station is a valid passenger station, non-passenger (e.g YARD, WYE etc),
    or unknown (e.g SRT stations, approaching Rosedale, spelling error).
    :param name: cleaned str of the station name
    :param valid_station_linecode: dictionary mapping valid passenger station to linecode
    :return: str indicating passenger, non-passenger or unknown
    """

    non_passenger_endname_keywords = ['YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
    if name in valid_station_linecode:
        category = "Passenger"
    elif name.split(' ')[-1] in non_passenger_endname_keywords:
        category = "Non-passenger"
    else:
        category = "Unknown" #e.g approaching Rosedale
    return category

def add_station_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Station Category' column to the DataFrame, labeling each station as
    'passenger', 'non-passenger', or 'unknown'.
    Drops rows with 'Station Category' labeled as 'unknown', which include:
      - SRT stations,
      - stations with severe spelling errors,
      - and stations with directionals (e.g., "to", "towards") making them ambiguous.
    :param df: pd.Dataframe
    :return: pd.Dataframe with added 'Station Category' column
    """
    valid_station_linecode = valid_station_linecode_dict()
    df['Station Category'] = df['Station'].apply(lambda station: categorize_station(station, valid_station_linecode))
    return df

def drop_unknown_stations(df:pd.DataFrame, dropped_raw_data_dir: str = DROPPED_RAW_DATA_DIR) -> pd.DataFrame:
    """
    Drops rows with 'Station Category' labeled as 'unknown', which include:
      - SRT stations,
      - stations with severe spelling errors,
      - and stations with directionals (e.g., "to", "towards") making them ambiguous.
    Logs the dropped rows.
    :param df: pd.Dataframe
    :param dropped_raw_data_dir: Directory to store dropped data
    :return: pd.Dataframe with added 'Station Category' column
    """
    prefix = "unknown_stations"
    dropped_df = df[df["Station Category"] == "Unknown"]
    file_utils.write_to_csv(df=dropped_df, prefix=prefix, output_dir=dropped_raw_data_dir)
    print(f"Rows dropped: unknown stations saved in {dropped_raw_data_dir}")

    return df[df["Station Category"] != "Unknown"].copy()

def drop_non_passenger_stations(df:pd.DataFrame, dropped_raw_data_dir: str = DROPPED_RAW_DATA_DIR) -> pd.DataFrame:
    """
    Drops rows with 'Station Category' labeled as 'non-passenger', which include:
      - Yards, Hostler, Track etc
    Logs the dropped rows.
    :param df: pd.Dataframe
    :param dropped_raw_data_dir: Directory to store dropped data
    :return: pd.Dataframe with added 'Station Category' column
    """
    prefix = "non_passenger"
    dropped_df = df[df["Station Category"] == "Non-passenger"]
    file_utils.write_to_csv(df=dropped_df, prefix=prefix, output_dir=dropped_raw_data_dir)
    print(f"Rows dropped: non-passenger stations saved in {dropped_raw_data_dir}")

    return df[df["Station Category"] != "Non-passenger"].copy()

def clean_linecode(row:pd.Series, valid_station_linecode:dict) -> str | float:
    """
    Fixes incorrect linecodes using the valid_station_linecode_dict.
    :param row: pd.Series
    :param valid_station_linecode: Dictionary containing operational station names with corresponding linecode
    :return: linecode or np.nan for ambiguous data
    """

    station = row["Station"]
    line = row["Line"]

    if station not in valid_station_linecode: # a non-passenger station or unknown
        return line

    # valid linecodes for the station
    valid_codes = valid_station_linecode[station]

    if line in valid_codes:
        return line # already the correct code

    if len(valid_codes) > 1: # Too ambiguous to fix. e.g. Bloor-Yonge subway,
        # if the linecode is not BD or YU, we wouldn't know which is the correct code
        return np.nan

    else: # fix to the correct code
        return valid_codes[0]  # Fix to the correct code

def clean_linecode_column(df: pd.DataFrame) -> pd.DataFrame:
    valid_station_linecode = valid_station_linecode_dict()
    df["Line"] = df.apply(lambda row: clean_linecode(row, valid_station_linecode), axis = 1)
    return df

def clean_bound(row:pd.Series, valid_station_linecode:dict) -> str | float:
    """
    For passenger stations with valid line codes e.g Rosedale: YU, check that Bound matches line's valid directions.
    Else set to NaN.
    :param row: row from pd.DataFrame with corrected linecode
    :param valid_station_linecode: Dictionary containing operational station names with corresponding linecode
    :return: bound or np.nan
    """
    line = row["Line"] # correct line
    bound = row["Bound"]

    if row["Station"] in valid_station_linecode  and line in VALID_LINECODES_TO_BOUND_DICT : # passenger station
        if bound not in VALID_LINECODES_TO_BOUND_DICT[line]:
            return np.nan # too ambiguous to fix direction

    return bound

def clean_bound_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    For passenger stations with valid line codes e.g Rosedale: YU, check that Bound matches line's valid directions.
    :param df: pd.DataFrame
    :return: pd.DataFrame with clean bound names
    """
    valid_station_linecode = valid_station_linecode_dict() # e.g {"Rosedale: "YU"}
    df["Bound"] = df.apply(lambda row: clean_bound(row, valid_station_linecode), axis = 1)

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

    d_parsed = pd.to_datetime(d, errors='coerce')  # standard inference (YYYY-MM-DD)

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

def add_isweekday(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a new column 'IsWeekday' to indicate whether each date falls on a weekday.

    :param df: pd.Dataframe with Datetime column
    :return: pd.Dataframe with added 'IsWeekday' column
    """
    df['IsWeekday'] = df['DateTime'].dt.weekday < 5  # True for weekdays, False for weekends
    return df

def categorize_rush_hour(row:  pd.Series, weekday_rush_hour:dict= WEEKDAY_RUSH_HOUR_DICT) -> str:
    """
    Categorizes rush hour into morning, afternoon, offpeak or weekend

    :param row: row from pd.DataFrame
    :param weekday_rush_hour: Dictionary with keys for start/end times of rush hours.
    :return: Rush hour category
    """

    if row['IsWeekday']:
        t = row['DateTime'].time()
        # Morning peak: 6am - 9am
        if  weekday_rush_hour["morning start"]  <= t < weekday_rush_hour["morning end"]:
            return "Morning"

        # Midday off-peak: 9am - 3pm
        elif weekday_rush_hour["morning end"]  <= t < weekday_rush_hour["evening start"]:
            return "Off-peak: Afternoon"

        # Evening peak: 3pm - 7pm
        elif weekday_rush_hour["evening start"]  <= t < weekday_rush_hour["evening end"]:
            return "Evening"

        # Night off-peak, 7pm onwards
        else:
            return "Off-peak: Night"

    else:
        return "Weekend"

def add_rush_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Rush Hour' column to the DataFrame, categorizing each row as
    'morning', 'evening', 'off peak', or 'weekend' based on the time and day.

    :param df: pd.DataFrame
    :return: df: pd.DataFrame with an added 'Rush Hour' column
    """
    df['Rush Hour'] =  df.apply(categorize_rush_hour, axis =1)
    return df

def get_season(dt: pd.Timestamp, seasons: Dict[str, List[int]] = SEASONS_TO_MONTHS_DICT) -> str:
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
    Loads a CSV file containing raw TTC delay code descriptions, removes all non-ASCII characters
    from the text fields, and saves a cleaned version to disk.

    This helps ensure the output file is encoding-safe and free of mojibake characters like â or Ã.

    The cleaned file is saved to:
    'data/raw/code_descriptions/Clean Code Descriptions.csv'

    :return: None
    """
    codes = pd.read_csv(CODE_DESCRIPTIONS_FILE, encoding='utf-8-sig')

    def remove_non_ascii(text):
        return re.sub(r'[^\x00-\x7F]+', '', text) if isinstance(text, str) else text

    codes_cleaned = codes.applymap(remove_non_ascii)
    filepath = os.path.join(RAW_CODE_DESC_DIR,"Clean Code Descriptions.csv")
    codes_cleaned.to_csv (filepath,index=False, encoding='utf-8-sig')

def delay_code_descriptions_dict() -> dict:
    """
    Creates a dictionary mapping delay codes to their descriptions.
    """
    filepath = os.path.join(RAW_CODE_DESC_DIR,"Clean Code Descriptions.csv")
    df = file_utils.read_csv(filepath)
    return df.set_index("CODE")["DESCRIPTION"].to_dict()


def clean_delay_code(row:pd.Series, delay_code_descriptions: dict, error_rows:list) -> str|float:
    """
    Cleans delay code by checking if it exists in the provided descriptions dictionary.
    If the delay code is not present in the dictionary, returns NaN.
    Logs rows with errors in delay code
    :param row: row of pd.Dataframe
    :param delay_code_descriptions: Dictionary mapping delay codes to their descriptions
    :param error_rows: list of rows containing delay code errors
    :return: correct delay code, or np.nan if not valid.
    """
    delay_code = row['Code']
    if delay_code not in delay_code_descriptions:
        error_rows.append(row.to_dict())
        return np.nan
    return delay_code

def clean_delay_code_column(df:pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the 'Code' column in a DataFrame by setting invalid delay codes to nan and
    logs rows with errors in delay code and saves error data to disk.
    :param df: pd.DataFrame
    :return: pd.DataFrame with cleaned 'Code' column
    """
    delay_code_descriptions = delay_code_descriptions_dict()
    error_rows = []
    # Sets errors to nan
    df['Code'] =\
        df.apply(lambda row: clean_delay_code(row, delay_code_descriptions, error_rows), axis = 1)
    # Save rows with errors to disk
    df_code_error = pd.DataFrame(error_rows)
    file_utils.write_to_csv(df_code_error, "delay_data_w_delay_code_error", DROPPED_RAW_DATA_DIR)
    return df

def delay_description(delay_code:str, delay_code_descriptions: dict) -> str:
    """
    Provide the description of the delay, e.g disorderly patron
    :param delay_code: code of the delay
    :param delay_code_descriptions: Dictionary mapping delay codes to their descriptions
    :return: code description
    """
    return delay_code_descriptions[delay_code]

def add_delay_description(df:pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Delay Description' column to pd.DataFrame
    :param df: pd.DataFrame
    :return: pd.DataFrame with 'Delay Description' column
    """
    delay_code_description = delay_code_descriptions_dict()
    df['Delay Description'] = df['Code'].apply(lambda code: delay_description(code, delay_code_description))
    return df

def sort_by_datetime(df:pd.DataFrame) -> pd.DataFrame:
    """
    Sort pd.DataFrame by DateTime
    :param df: pd.DataFrame containing DateTime column
    :return: pd.DataFrame sorted by DateTime
    """
    return df.sort_values(by='DateTime')

def delay_code_category_dict() -> dict:
    """
    Creates a dictionary mapping delay codes to their categories. Using manually edited Clean Code Descriptions.csv
    """
    df = file_utils.read_csv(PROCESSED_CODE_DESCRIPTIONS_FILE)
    return dict(zip(df["CODE"], df["CATEGORY"]))

def delay_category(row:pd.Series, delay_code_category: dict, error_rows:list) -> str|float:
    """
    Gets the category for the delay code
    :param row: row of pd.DataFame
    :param delay_code_category: dictionary mapping delay code to category e.g Mechanical/Infrastructure
    :param error_rows: list of rows containing delay code errors
    :return category of delay code or np.nan
    """
    delay_code = row["Code"]
    if delay_code not in delay_code_category:
        error_rows.append(row.to_dict())
        return np.nan
    return delay_code_category[delay_code]

def add_delay_category(df:pd.DataFrame) -> pd.DataFrame:
    """
    Adds delay category column to pd.DataFrame
    :param df:  pd.DataFrame
    :return: pd.DataFrame with delay category column
    """
    delay_code_category = delay_code_category_dict()
    error_rows = []
    df['Delay Category'] = df.apply(lambda row: delay_category(row, delay_code_category, error_rows), axis = 1)
    # Save rows with errors to disk
    df_code_error = pd.DataFrame(error_rows)
    file_utils.write_to_csv(df_code_error, "delay_data_w_delay_category_error", DROPPED_RAW_DATA_DIR)
    df = df.dropna()
    return df

def name_change(df: pd.DataFrame) -> pd.DataFrame   :
    """
    Rename stations according to latest City of Toronto names. e.g. Dundas -> TMU
    :param df: pd.DataFrame
    :return: pd.DateFrame with latest names
    """
    df["Station"] = df["Station"].replace(NAME_CHANGES)
    return df
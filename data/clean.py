import ast
import re
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import os

from config import (DELAY_DATA, VALID_STATIONS_LIST, VALID_STATIONS_WITH_LINECODES, CODE_DESCRIPTIONS, LOG_DIR,
                    REFERENCE_COLS_ORDERED)
BASE_DIR = r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit'
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'delays')

log_path = os.path.join(LOG_DIR, f'')
years = range(2018, 2025)

# list of excel file data from 2018-2024
excel_files = [os.path.join(RAW_DATA_DIR, f'ttc-subway-delay-data-{year}.xlsx') for year in years]
csv_file = os.path.join(RAW_DATA_DIR, 'delays', 'TTC Subway Delay Data since 2025.csv')

dfs = []
for file in excel_files:
    if os.path.exists(file):
        df = pd.read_excel(file)
        dfs.append(df)
    else:
        print(f"Warning: File not found - {file}")

if os.path.exists(csv_file):
    df_2025 = pd.read_csv(csv_file)
    dfs.append(df_2025)
else:
    print(f"Warning: 2025 file not found - {csv_file}")

for i, df in enumerate(dfs):
    print(f"File {i} columns: {list(df.columns)}")
print(len(dfs))

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'delay_merge_log_{timestamp}.txt'

def clean_merge_delay_data(dfs: list[pd.DataFrame], log_filename: str,
                           reference_cols_ordered: list[str]= REFERENCE_COLS_ORDERED, verbose: bool = True):
    """
    Validates and merges delay dataframes.
    :param dfs: List of raw pandas DataFrames to merge.
    :param reference_cols_ordered: Expected column names in the desired order.
    :param log_path: Path to a log file. If None, logs are not saved.
    :param verbose: Whether to print status messages during processing.
    :return: pd.DataFrame: A single cleaned, merged dataframe.
    """
    reference_cols_set = set(reference_cols_ordered)
    log_path = os.path.join(LOG_DIR, log_filename)

    log_lines = []

    for i, df in enumerate(dfs):
        current_cols = set(df.columns)
        if current_cols != reference_cols_set:
            missing = reference_cols_set - current_cols
            extra = current_cols - reference_cols_set
            log_lines.append(f"File {i} has issues:")
            if missing:
                log_lines.append(f"   Missing columns: {missing}")
            if extra:
                log_lines.append(f"   Extra columns:   {extra}")

        else:
            # If no issues, reindex to match the reference column order
            dfs[i] = dfs[i].reindex(columns=reference_cols_ordered)

    if log_lines:
        if verbose:
            print("\nInconsistent column sets found:")
            for line in log_lines:
                print(line)
    else:
        message = "All files contain the correct columns (regardless of order)."
        if verbose:
            print("\n" + message)
        log_lines.append(message)


    with open(log_path, 'w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')



    combined_df = pd.concat(dfs, ignore_index=True)

    if verbose:
        print("Merged DataFrame shape:", combined_df.shape)
        print("Preview:")
        print(combined_df.head())

    return combined_df

# df = pd.read_csv(DELAY_DATA)
# # print(len(df))
# # print(df[df['Station'].str.contains("bloor", case=False, na=False)]['Station'].unique())
# # print(df[df['Station'].str.contains("yonge", case=False, na=False)]['Station'].unique())
# df = df[df['Min Delay'] != 0]
# df = df.dropna()
# # drop data that doesn't have a clear line
# valid_line_codes = {
#   'YU': 'Line 1',
#   'BD': 'Line 2',
#   'SHP': 'Line 4',
# }
# df = df[df['Line'].str.upper().isin(valid_line_codes)]
#
# # reset index
# df.reset_index(drop=True, inplace=True)
#
#
#
# # print(df.columns)
# # print(df['Bound'].unique()) # need to do this check when all of the dfs are combined later, make sure the bound is consistent
# # print(df['Line'].unique())
# # print(df['Station'].unique())
# # print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# # df['Station'] = df['Station'].str.replace(r'union.*', 'UNION STATION', flags=re.IGNORECASE, regex=True)
# # print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# # print(df[df['Station'].str.contains("kennedy", case=False, na=False)]['Station'].unique())
# # # check bound names
#
# df['last_word'] = df['Station'].astype(str).str.strip().str.split().str[-1]
#
# print(df['last_word'].value_counts())
#
# def clean_station_name(name:str) -> str:
#     """
#     clean and standardize the TTC station name, e.g UNION STATION TOWARD K, becomes UNION STATION
#     :param name: name of the TTC station
#     :return: clean name of the TTC station
#     """
#
#     name = str(name).strip().upper() # strips leading and trailing white spaces, makes everything upper case
#     name = re.sub(r'\s+', ' ', name) # replaces any spaces that are one or more tabs in the name to one
#
#     # Handle directional indicators
#     for directional in [' TO ', ' TOWARD ', ' TOWARDS ']:
#         if directional in name:
#             name = name.split(directional)[0]
#
#     # Remove directional name, e.g DAVISVILLE - some other station
#     if ' - ' in name and name not in ['SHEPPARD - YONGE', 'BLOOR - YONGE']:
#         name = name.split( ' - ')[0]
#
#
#     # Normalize 'St' to 'St.'
#     name = re.sub(r'\bST\b(?=\s)', 'ST.', name)
#
#     # Remove trailing parentheticals like "(TO KING)"
#     name = re.sub(r'\(.*?\)', '', name) # closed (TO KING)
#     name = re.sub(r'\(.*', '', name) # unclosed (TO KING
#
#     # Remove embedded line codes (YUS, BD, L1, L2, etc.) from anywhere in the name
#     name = re.sub(r'\b(YU|YUS|BD|BDL|BDN|BD-S|L1|L2|LINE\s?\d+)\b', '', name)
#
#     # clean up extra whitespace left behind
#     name = re.sub(r'\s+', ' ', name)
#
#
#     # Fix endings like "STATIO", "STA", etc.
#     name = name.strip() # remove white spaces in the beginning and the end
#     if name.endswith(" STATIO") or name.endswith(" STA"):
#         name = re.sub(r'( STATIO| STA)$', ' STATION', name)
#
#
#     legit_station_endname_keywords = ['STATION', 'YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
#     if name.split(' ')[-1] not in legit_station_endname_keywords:
#         name += ' STATION'
#
#
#     # Fixes abbreviations and Dual Named Interchange Stations
#     station_map = {
#         'VMC STATION': 'VAUGHAN METROPOLITAN CENTRE STATION',
#         'VAUGHAN MC STATION': 'VAUGHAN METROPOLITAN CENTRE STATION',
#         'NORTH YORK CTR STATION': 'NORTH YORK CENTRE STATION',
#         'BLOOR STATION': 'BLOOR-YONGE STATION',
#         'YONGE STATION': 'BLOOR-YONGE STATION',
#         'YONGE-UNIVERSITY AND B': 'BLOOR-YONGE STATION',
#         'SHEPPARDYONGE STATION': 'SHEPPARD-YONGE STATION',
#         'SHEPPARD STATION': 'SHEPPARD-YONGE STATION',
#         'YONGE SHEP STATION': 'SHEPPARD-YONGE STATION',
#         'YONGE SHP STATION': 'SHEPPARD-YONGE STATION',
#         'SHEPPARD YONGE STATION': 'SHEPPARD-YONGE STATION'}
#
#     key = name.strip().upper()
#     if key in station_map:
#         name = station_map[key]
#
#     # clean up extra whitespace left behind
#     name = re.sub(r'\s+', ' ', name)
#     # Fix spelling error for Station
#
#     return name
#
#
#     # to do: clean to, clean Yard(this is ligit, keep yard as non-station, what is WYE, check any name not
#     # ending with station
#     # remove stations that are McCowan or Lawrence East
#
# def categorzie_station(name:str) -> str:
#     """
#     This function checks if a station is a passenger station, non-passenger (e.g YARD, WYE etc),
#     or unknown (e.g approaching Rosedale, spelling error)
#     :param name: cleaned str of the station name
#     :return: str indicating passenger, non-passenger or unknown
#     """
#     # load the valid stations list
#     with open(VALID_STATIONS_LIST) as f:
#         valid_stations = {line.strip().upper() for line in f if line.strip()}
#     name = name.strip().upper()
#
#     non_passenger_endname_keywords = ['YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
#     if name in valid_stations:
#         category = "passenger station"
#     elif name.split(' ')[-1] in non_passenger_endname_keywords:
#         category = "non-passenger station"
#     else:
#         category = "unknown" #e.g approaching Rosedale
#     return category
#
#
# def valid_station_linecode_dict() -> dict:
#     valid_station_linecode = {}
#     with open(VALID_STATIONS_WITH_LINECODES) as f:
#         for line in f:
#             if line.strip(): # non-empty
#                 name, linecode = line.upper().split("STATION")
#                 valid_station_linecode[name + "STATION"] = ast.literal_eval(linecode.strip())
#     return valid_station_linecode
#
# def clean_linecode(df):
#     """
#     This function will fix incorrect linecodes using the valid_station_linecode_dict.
#     :param name: cleaned station name
#     :param linecode: the line data for that station
#     :return: name and correct linecode
#     """
#     valid_station_linecode = valid_station_linecode_dict()
#
#     for index, row in df.iterrows():
#         station = row["Station"]
#         line = row["Line"]
#
#         if station not in valid_station_linecode: # a non-passenger station
#             continue
#
#         valid_codes = valid_station_linecode[station]
#
#         if line in valid_codes:
#             continue # already the correct code
#
#         if len(valid_codes) > 1: # Too ambiguous to fix. e.g. Bloor-Yonge subway,
#             # if the linecode is not BD or YU, we wouldn't know which is the correct code
#             df.at[index, "Line"] = np.nan
#
#         else: # fix to the correct code
#             df.at[index, "Line"] = valid_codes[0]  # Fix to the correct code
#
#     return df
#
# def add_datetime(df):
#     """
#     Converts 'Date' and 'Time' columns into proper date and time objects,
#     then combines them into a single 'DateTime' column.
#
#     This enables easier extraction of time-based features such as hour, day of week, etc.
#     :param df: pandas DataFrame with 'Date' and 'Time' columns as strings
#     :return: pandas DataFrame with added 'DateTime' column
#     """
#     df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time
#     df['Date'] = pd.to_datetime(df['Date']).dt.date
#     df['DateTime'] = df.apply(lambda row: datetime.combine(row['Date'], row['Time']), axis=1)
#     return df
#
#
#
# def clean_day(df):
#     """
#      Extracts the day of the week from the 'Date' column and stores it in a 'Day' column. This will fix any errors
#      in the 'Day' column.
#
#     :param df: pandas DataFrame with a 'Date' column (datetime64[ns])
#     :return: pandas DataFrame with added or updated 'Day' column
#     """
#     df['Day'] = df['Date'].dt.day_name()
#     return df
#
# def add_IsWeekday(df):
#     """
#     Adds a new column 'IsWeekday' to indicate whether each date falls on a weekday.
#     :param df:
#     :return:
#     """
#     df['IsWeekday'] = df['Date'].dt.weekday < 5  # True for weekdays, False for weekends
#     return df
#
# def clean_delay_code_descriptions():
#     """
#     Loads a CSV file containing TTC delay code descriptions, removes all non-ASCII characters
#     from the text fields, and saves a cleaned version to disk.
#
#     This helps ensure the output file is encoding-safe and free of mojibake characters like â or Ã.
#
#     The cleaned file is saved to:
#     'data/raw/code_descriptions/Clean Code Descriptions.csv'
#
#     :return: None
#     """
#     codes = pd.read_csv(CODE_DESCRIPTIONS, encoding='utf-8-sig')
#
#     def remove_non_ascii(text):
#         return re.sub(r'[^\x00-\x7F]+', '', text) if isinstance(text, str) else text
#
#     codes_cleaned = codes.applymap(remove_non_ascii)
#     (codes_cleaned.to_csv
#      (r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\code_descriptions\Clean Code Descriptions.csv',
#       index=False, encoding='utf-8-sig'))
#
#
# # clean_delay_code_descriptions()
#
# # def code_descriptions_dict():
# #     with open(code_descriptions_list) as f:
#
#
# # df = pd.read_excel(code_descriptions_list, header=None)
#
#
# # View the first few rows
#
#
# # df = add_datetime(df)
# # df['Day'] = df.apply(lambda row: row['Date'].strftime('%A'), axis=1)
# # # names in df['Station']:
# # # cleaned_name = clean_station_name(names)
# # # station_names.append(cleaned_name)
# # station_names = []
# # for names in df['Station']:
# #     cleaned_name = clean_station_name(names)
# #     station_names.append(cleaned_name)
# #
# # # print(set(station_names))
# # name_cat ={}
# # for name in station_names:
# #     if name not in name_cat:
# #         name_cat[name] = categorzie_station(name)
# #
# # error_in_linecode = {}
# # df['Station'] = df['Station'].apply(clean_station_name)
# #
# #
# #
# # valid_station_linecode = valid_station_linecode_dict()
# #
# # for index, row in df.iterrows():
# #     if row["Station"] in valid_station_linecode:
# #         if row['Line'] in valid_station_linecode[row["Station"]]:
# #             pass
# #         else:
# #             error_in_linecode[row['Station']] = (row['Line'], valid_station_linecode[row["Station"]])
# #
# #
# # print(error_in_linecode)
# #
# # error_in_linecode = {}
# # df_clean = clean_linecode(df)
# # for index, row in df_clean.iterrows():
# #     if row["Station"] in valid_station_linecode:
# #         if row['Line'] in valid_station_linecode[row["Station"]]:
# #             pass
# #         else:
# #             error_in_linecode[row['Station']] = (row['Line'], valid_station_linecode[row["Station"]])
# #
# #
# # print(error_in_linecode)
# # #to do, clean up the line codes, for Kennedy special case, SRT, ignore, we will be deleting later
# # # fix time date
# # # merge all the csv, make sure they have the same columns
# #
# # print(df['Time'].head())
# # print(df['Date'].head())
# # print(df['DateTime'].head())
#
# print(df['Bound'].unique())
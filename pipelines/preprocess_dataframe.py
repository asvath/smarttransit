import os

import numpy as np
import pandas as pd


from utils import load_utils, clean_utils, log_utils, file_utils
from config import LOG_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR

"""
Preprocesses TTC subway delay data.

This script performs the following:
- Merges multiple raw delay data files
- Removes invalid records (e.g., NaNs, zero-minute delays, missing vehicle numbers)
- Cleans and standardizes key fields (e.g., station names, delay codes, bounds)
- Adds helper columns such as station category and `is_weekend`
- Saves the cleaned DataFrame to the processed data directory

For manual verification purposes, the script also logs:
- Names of raw delay data files merged, along with any errors during merging (e.g., missing or extra columns)
- Unique stations by category (passenger, non-passenger, unknown)
- Station names containing directionals (e.g., "to", "towards", "toward")
"""

merged_file_name = "merged_unfiltered"
clean_file_name = "cleaned_delay_data"

def clean_dataframe():
    """
    Cleans and saves DataFrame to disk.
    :return:pd.DataFrame: cleaned DataFrame
    """

    # load the raw delay data
    dfs, files_loaded = load_utils.load_raw_data_files()

    # merge the dataframes
    df_merged = clean_utils.merge_delay_data(dfs, files_loaded)

    # save to interim folder
    merged_file_path = file_utils.write_to_csv(df_merged, merged_file_name, INTERIM_DATA_DIR, True)

    # load merged unfiltered data
    df = file_utils.read_csv(merged_file_path)

    # drop nan data and data with no delay, no gap, delay < time gap between trains or no vehicle number
    df = clean_utils.drop_invalid_rows(df)

    # standardize station names
    df = clean_utils.clean_station_column(df)

    # categorize stations into passenger, non-passenger and unknown
    df = clean_utils.add_station_category(df)

    # drop stations that are SRT stations or have severe spelling errors, or have directionals in the name
    df = clean_utils.drop_unknown_stations(df)


    df = clean_utils.clean_delay_code_column(df)
    # print(df.head())
    # print(df.columns)
    # Print all rows where "Code" is NaN

    #
    # # clean linecode
    # df = clean_utils.clean_linecode_column(df)
    #
    # # Clean bound
    # df = clean_utils.clean_bound_column(df)
    #
    # # add datetime column
    # df = clean_utils.clean_and_add_datetime(df)
    #
    # # Remove any rows where Date, Time, or DateTime have missing values after parsing
    # df = df.dropna()
    #
    # # clean day
    # df = clean_utils.clean_day(df)
    #
    # # add IsWeekday column
    # df = clean_utils.add_IsWeekday(df)
    #
    # # add rush hour column
    # df = clean_utils.add_rush_hour(df)
    #
    # # add season column
    # df = clean_utils.add_season(df)
    #
    # # Remove any invalid rows after cleaning data
    # df = df.dropna()
    #
    # # Log unique stations by category
    # log_utils.log_unique_stations_by_category(df, LOG_DIR)
    #
    # # Log stations which directional names
    # log_utils.log_station_names_with_directionals(df, LOG_DIR)
    #
    # # Write out cleaned csv
    # file_utils.write_to_csv(df, clean_file_name, PROCESSED_DATA_DIR, True)
    #
    # print(f"Cleaned and saved dataframe {clean_file_name} in {PROCESSED_DATA_DIR}")

    return df

if __name__=="__main__":
    clean_dataframe()
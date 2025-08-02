import os
import pandas as pd


from utils import load_utils, clean_utils, log_utils
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

merged_file_name = os.path.join(INTERIM_DATA_DIR, "merged_unfiltered.csv")
clean_file_name = os.path.join(PROCESSED_DATA_DIR, "cleaned_delay_data.csv")

def clean_dataframe():

    # load the raw delay data
    dfs, files_loaded = load_utils.load_raw_data_files()

    # merge the dataframes
    df_merged = clean_utils.merge_delay_data(dfs, files_loaded)

    # save to interim folder
    df_merged.to_csv(merged_file_name, index=False)

    # load merged unfiltered data
    df = pd.read_csv(merged_file_name)

    # drop nan data and data with no delay or no vehicle number
    df = clean_utils.drop_invalid_rows(df)

    # standardize station names
    df = clean_utils.clean_station_column(df)


    # categorize stations into passenger, non-passenger and unknown
    df = clean_utils.add_station_category(df)

    # clean linecode
    df = clean_utils.clean_linecode(df)

    # Clean bound
    df = clean_utils.clean_bound(df)


    # add datetime column
    df = clean_utils.clean_and_add_datetime(df)


    # Inspect a few failed rows if any:
    df.loc[df['DateTime'].isna(), ['Date', 'Time']].head(5)

    # Remove any rows where Date, Time, or DateTime have missing values after parsing
    df = df.dropna()


    # clean day
    df = clean_utils.clean_day(df)

    # add IsWeekday column
    df = clean_utils.add_IsWeekday(df)


    # Remove any rows after cleaning data
    df = df.dropna()

    # Log unique stations by category
    log_utils.log_unique_stations_by_category(df, LOG_DIR)

    # Log stations which directional names
    log_utils.log_station_names_with_directionals(df, LOG_DIR)

    # Write out cleaned csv
    df.to_csv(clean_file_name, index=False)

    print(f"Cleaned and saved dataframe {clean_file_name}")


if __name__=="__main__":
    clean_dataframe()
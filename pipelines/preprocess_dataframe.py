import os

import pandas as pd

from utils import load_utils, clean_utils, log_utils
from config import DATA_DIR, LOG_DIR

interim_dir = os.path.join(DATA_DIR, "interim")
processed_dir = os.path.join(DATA_DIR, "processed")
merged_file_name = os.path.join(interim_dir, "merged_unfiltered.csv")
clean_file_name = os.path.join(processed_dir, "cleaned_delay_data.csv")

# # load the raw delay data
# dfs, files_loaded = load_utils.load_raw_data_files()
#
# # merge the dataframes
# df_merged = clean_utils.merge_delay_data(dfs, files_loaded)
#
# # save to interim folder
# df_merged.to_csv(merged_file_name, index=False)

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

# add datetime column
df = clean_utils.clean_and_add_datetime(df)

# Remove any rows where Date, Time, or DateTime have missing values after parsing
df = df.dropna()

# clean day
df = clean_utils.clean_day(df)

# add IsWeekday column
df = clean_utils.add_IsWeekday(df)

# Clean bound
df = clean_utils.clean_bound(df)

# Remove any rows after cleaning data
df = df.dropna()

# Log unique stations by category
df = log_utils.log_unique_stations_by_category(df, LOG_DIR)

# Log stations which directional names
df = log_utils.log_station_names_with_directionals(df, LOG_DIR)

# Write out cleaned csv
df.to_csv(clean_file_name, index=False)
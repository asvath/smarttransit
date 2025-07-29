import os

import pandas as pd

from utils import load_utils, clean_utils
from config import DATA_DIR, LOG_DIR

interim_dir = os.path.join(DATA_DIR, "interim")
file_name = os.path.join(interim_dir, "merged_unfiltered.csv")

# # load the raw delay data
# dfs, files_loaded = load_utils.load_raw_data_files()
#
# # merge the dataframes
# df_merged = clean_utils.merge_delay_data(dfs, files_loaded)
#
# # save to interim folder
# df_merged.to_csv(file_name, index=False)

# load merged unfiltered data
df = pd.read_csv(file_name)

# drop nan data and data with no delay
df = df.dropna()
df = df[df['Min Delay'] != 0]


# standardize station names
df['Station'] = df['Station'].apply(clean_utils.clean_station_name)

# categorize stations into passenger, non-passenger and unknown
df['Station Category'] = df['Station'].apply(clean_utils.categorzie_station)
print(df['Station Category'].value_counts())

# # Log unique stations by category
# for category in ['passenger', 'non-passenger', 'unknown']:
#     stations_in_category = df[df['Station Category'] == category]['Station'].unique()
#     stations_in_category.sort()
#     with open(f'{LOG_DIR}/stations_{category}.txt', 'w', encoding='utf-8') as f:
#         for station in stations_in_category:
#             f.write(station + '\n')
#
# mask = df['Station'].str.contains(r'\b(to|toward|towards)\b', case=False, na=False)
# station_spans = df[mask]
# print(station_spans['Station'])
# print(station_spans.shape[0])
# log_path = os.path.join(LOG_DIR, "station_spans_with_to_towardx.txt")

# with open(log_path, "w", encoding="utf-8") as f:
#     for station in station_spans['Station'].unique():
#         f.write(station + "\n")
#
# print(f"Logged {len(station_spans)} station span entries to {log_path}")

# clean linecode

df = clean_utils.clean_linecode(df)

# add datetime column
df = clean_utils.add_datetime(df)

# clean day

df = clean_utils.clean_day(df)

# add IsWeekday column
df = clean_utils.add_IsWeekday(df)

# print(df.head())
# df = df.dropna()
#
# print(df['Bound'].unique())
# print(df['Vehicle'].value_counts())
# print(df[df['Vehicle'] == 6181]['Code'].value_counts())
#
# print(df[df['Vehicle'] == 5796]['Code'].value_counts())
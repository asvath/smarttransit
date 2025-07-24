import ast
import re

import numpy as np
import pandas as pd
import os

raw_data_dir= r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\delays'
valid_stations_list= r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\docs\ttc_subway_stations.txt'
valid_stations_list_w_linecode =\
    r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\docs\ttc_subway_stations_with_linecodes.txt'
filename = 'TTC Subway Delay Data since 2025.csv'
filepath = os.path.join(raw_data_dir, filename)

df = pd.read_csv(filepath)
print(len(df))
print(df[df['Station'].str.contains("bloor", case=False, na=False)]['Station'].unique())
print(df[df['Station'].str.contains("yonge", case=False, na=False)]['Station'].unique())
df = df[df['Min Delay'] != 0]
df = df.dropna()
# drop data that doesn't have a clear line
valid_line_codes = {
  'YU': 'Line 1',
  'BD': 'Line 2',
  'SHP': 'Line 4',
}
df = df[df['Line'].str.upper().isin(valid_line_codes)]

# reset index
df.reset_index(drop=True, inplace=True)



# print(df.columns)
# print(df['Bound'].unique()) # need to do this check when all of the dfs are combined later, make sure the bound is consistent
# print(df['Line'].unique())
# print(df['Station'].unique())
# print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# df['Station'] = df['Station'].str.replace(r'union.*', 'UNION STATION', flags=re.IGNORECASE, regex=True)
# print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# print(df[df['Station'].str.contains("kennedy", case=False, na=False)]['Station'].unique())
# # check bound names

df['last_word'] = df['Station'].astype(str).str.strip().str.split().str[-1]

print(df['last_word'].value_counts())

def clean_station_name(name:str) -> str:
    """
    clean and standardize the TTC station name, e.g UNION STATION TOWARD K, becomes UNION STATION
    :param name: name of the TTC station
    :return: clean name of the TTC station
    """

    name = str(name).strip().upper() # strips leading and trailing white spaces, makes everything upper case
    name = re.sub(r'\s+', ' ', name) # replaces any spaces that are one or more tabs in the name to one

    # Handle directional indicators
    for directional in [' TO ', ' TOWARD ', ' TOWARDS ']:
        if directional in name:
            name = name.split(directional)[0]

    # Remove directional name, e.g DAVISVILLE - some other station
    if ' - ' in name and name not in ['SHEPPARD - YONGE', 'BLOOR - YONGE']:
        name = name.split( ' - ')[0]


    # Normalize 'St' to 'St.'
    name = re.sub(r'\bST\b(?=\s)', 'ST.', name)

    # Remove trailing parentheticals like "(TO KING)"
    name = re.sub(r'\(.*?\)', '', name) # closed (TO KING)
    name = re.sub(r'\(.*', '', name) # unclosed (TO KING

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


    # to do: clean to, clean Yard(this is ligit, keep yard as non-station, what is WYE, check any name not
    # ending with station
    # remove stations that are McCowan or Lawrence East

def categorzie_station(name:str) -> str:
    """
    This function checks if a station is a passenger station, non-passenger (e.g YARD, WYE etc),
    or unknown (e.g approaching Rosedale, spelling error)
    :param name: cleaned str of the station name
    :return: str indicating passenger, non-passenger or unknown
    """
    # load the valid stations list
    with open(valid_stations_list) as f:
        valid_stations = {line.strip().upper() for line in f if line.strip()}
    name = name.strip().upper()

    non_passenger_endname_keywords = ['YARD', 'HOSTLER', 'WYE', 'POCKET', 'TAIL', 'TRACK']
    if name in valid_stations:
        category = "passenger station"
    elif name.split(' ')[-1] in non_passenger_endname_keywords:
        category = "non-passenger station"
    else:
        category = "unknown" #e.g approaching Rosedale
    return category


def valid_station_linecode_dict() -> dict:
    valid_station_linecode = {}
    with open(valid_stations_list_w_linecode) as f:
        for line in f:
            if line.strip(): # non-empty
                name, linecode = line.upper().split("STATION")
                valid_station_linecode[name + "STATION"] = ast.literal_eval(linecode.strip())
    return valid_station_linecode

def clean_linecode(df):
    """
    This function will fix incorrect linecodes using the valid_station_linecode_dict.
    :param name: cleaned station name
    :param linecode: the line data for that station
    :return: name and correct linecode
    """
    valid_station_linecode = valid_station_linecode_dict()

    for index, row in df.iterrows():
        station = row["Station"]
        line = row["Line"]

        if station not in valid_station_linecode: # a non-passenger station
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


# names in df['Station']:
# cleaned_name = clean_station_name(names)
# station_names.append(cleaned_name)
station_names = []
for names in df['Station']:
    cleaned_name = clean_station_name(names)
    station_names.append(cleaned_name)

# print(set(station_names))
name_cat ={}
for name in station_names:
    if name not in name_cat:
        name_cat[name] = categorzie_station(name)

error_in_linecode = {}
df['Station'] = df['Station'].apply(clean_station_name)



valid_station_linecode = valid_station_linecode_dict()

for index, row in df.iterrows():
    if row["Station"] in valid_station_linecode:
        if row['Line'] in valid_station_linecode[row["Station"]]:
            pass
        else:
            error_in_linecode[row['Station']] = (row['Line'], valid_station_linecode[row["Station"]])


print(error_in_linecode)

error_in_linecode = {}
df_clean = clean_linecode(df)
for index, row in df_clean.iterrows():
    if row["Station"] in valid_station_linecode:
        if row['Line'] in valid_station_linecode[row["Station"]]:
            pass
        else:
            error_in_linecode[row['Station']] = (row['Line'], valid_station_linecode[row["Station"]])


print(error_in_linecode)
#to do, clean up the line codes, for Kennedy special case, SRT, ignore, we will be deleting later
# fix time date
# merge all the csv, make sure they have the same columns

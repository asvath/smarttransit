import re
import pandas as pd
import os

raw_data_dir= r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\delays'
filename = 'TTC Subway Delay Data since 2025.csv'
filepath = os.path.join(raw_data_dir, filename)

df = pd.read_csv(filepath)
print(len(df))
df = df[df['Min Delay'] != 0]
df = df.dropna()


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

def clean_station_name(name:str):
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


    # to do: clean to, clean Yard(this is ligit, keep yard as non-station, what is WYE, check any name not ending with station
    # remove stations that are McCowan or Lawrence East
station_names = []
for names in df['Station']:
    cleaned_name = clean_station_name(names)
    station_names.append(cleaned_name)

print(set(station_names))
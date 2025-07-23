import re

import pandas
import pandas as pd
import os
raw_data_dir= r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit\data\raw\delays'
filename = 'TTC Subway Delay Data since 2025.csv'
filepath = os.path.join(raw_data_dir, filename)

df = pandas.read_csv(filepath)
print(len(df))
df = df[df['Min Delay'] != 0]
df = df.dropna()


# reset index
df.reset_index(drop=True, inplace=True)
print(df.columns)
print(df['Bound'].unique()) # need to do this check when all of the dfs are combined later, make sure the bound is consistent
print(df['Line'].unique())
print(df['Station'].unique())
print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# df['Station'] = df['Station'].str.replace(r'union.*', 'UNION STATION', flags=re.IGNORECASE, regex=True)
# print(df[df['Station'].str.contains("union", case=False, na=False)]['Station'].unique())
# print(df[df['Station'].str.contains("kennedy", case=False, na=False)]['Station'].unique())
# # check bound names

def clean_station_name(name:str):
    """
    clean the TTC station name, e.g UNION STATION TOWARD K, becomes UNION STATION
    :param name: name of the TTC station
    :return: clean name of the TTC station
    """

    name = str(name).strip().upper() # strips leading and trailing white spaces
    name = re.sub(r'\s+', ' ', name) # replaces any spaces that are one or more tabs in the name to one
    name = re.sub(r'\s+', ' ', name)
    # to do: clean to, clean Yard(this is ligit, keep yard as non-station, what is WYE, check any name not ending with station

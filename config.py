import os
from datetime import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Root of project

DATA_DIR = os.path.join(BASE_DIR, 'data')                   # Main data directory
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')        # All raw data, includes delays, docs, code_descriptions
RAW_DOCS_DIR = os.path.join(RAW_DATA_DIR, 'docs')               # Documentation or reference files
RAW_CODE_DESC_DIR = os.path.join(RAW_DATA_DIR, 'code_descriptions')  # Code descriptions (raw)
LOG_DIR = os.path.join(BASE_DIR, 'logs')                    # Logs directory
DROPPED_RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'dropped_raw')  # Dropped/invalid data
RAW_DELAY_DIR = os.path.join(RAW_DATA_DIR, 'delays')       # Raw delay data files
EXPORTS_DIR = os.path.join(BASE_DIR,'exports')             # Export directory for stats and plots, for website

# Processed data directories
INTERIM_DATA_DIR = os.path.join(DATA_DIR, 'interim') # Data mid-pipeline
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed') # Fully processed data dir
PROCESSED_DELAY_DIR = os.path.join(PROCESSED_DIR, 'delays') # processed delay data files
PROCESSED_CODE_DESC_DIR = os.path.join(PROCESSED_DIR, 'code_descriptions') # processed delay data files
EXPORTS_STATS_DIR = os.path.join(EXPORTS_DIR, 'json') # stats for website
EXPORTS_PLOTS_DIR = os.path.join(EXPORTS_DIR, 'plots') # plots for website

# File paths
# Contains operational passenger stations
VALID_STATIONS_FILE = os.path.join(RAW_DOCS_DIR, 'ttc_subway_stations.txt')
# Contains operational passenger stations with line codes
VALID_STATIONS_W_LINECODES_FILE = os.path.join(RAW_DOCS_DIR, 'ttc_subway_stations_with_linecodes.txt')

# Contains raw delay codes and descriptions
CODE_DESCRIPTIONS_FILE = os.path.join(RAW_CODE_DESC_DIR, 'Code Descriptions.csv')
PROCESSED_CODE_DESCRIPTIONS_FILE = os.path.join(PROCESSED_CODE_DESC_DIR, 'TTC_Delay_Codes_Categories_and_Reasoning.csv')

# Others
# Column names (in order) used for merging raw TTC delay data files
REFERENCE_COLS_ORDERED = [
    'Date', 'Time', 'Day', 'Station', 'Code',
    'Min Delay', 'Min Gap', 'Bound', 'Line', 'Vehicle'
]

# Valid bounds:
VALID_BOUND_LIST = ['N', 'S', 'E', 'W']

# Mapping linecode to bound
VALID_LINECODES_TO_BOUND_DICT = {"YU" : ["N", "S"], "BD" : ["E", "W"], "SHP" : ["E", "W"]}

# Mapping of rush hour to time objects
WEEKDAY_RUSH_HOUR_DICT = {
    "morning start": time(6, 0),
    "morning end" : time(9, 0),
    "evening start": time(15, 0),
    "evening end": time(19, 0)
}

# Mapping season to month
SEASONS_TO_MONTHS_DICT = {"Spring": [3,4,5], # "March", "April", "May"
           "Summer": [6,7,8] ,#"June", "July", "August",
           "Fall" : [9,10,11] ,#"September", "October", "November"
           "Winter": [12,1,2]} #["December", "January", "February"

VALID_UNITS = {"minutes", "hours", "days"}

CONVERSION_FACTORS = {
    "minutes": 1,
    "hours": 60,
    "days": 60 * 24,
}

NAME_CHANGES = {
    "DUNDAS STATION" : "TMU STATION",
    "EGLINTON WEST STATION": "CEDARVALE STATION"
}
import os
from datetime import time

# Base directory
BASE_DIR = r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit'
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DOCS_DIR = os.path.join(RAW_DATA_DIR, 'docs')
CODE_DESC_DIR = os.path.join(RAW_DATA_DIR, 'code_descriptions')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DROPPED_RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'dropped_raw')

# Data Directory
DELAY_DATA_DIR = os.path.join(RAW_DATA_DIR, 'delays')

# Processed data directories
INTERIM_DATA_DIR = os.path.join(DATA_DIR, 'interim')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')

# File paths
VALID_STATIONS_LIST = os.path.join(DOCS_DIR, 'ttc_subway_stations.txt')
VALID_STATIONS_WITH_LINECODES = os.path.join(DOCS_DIR, 'ttc_subway_stations_with_linecodes.txt')
CODE_DESCRIPTIONS = os.path.join(CODE_DESC_DIR, 'Code Descriptions.csv')

# Column names (in order) used for merging raw TTC delay data files
REFERENCE_COLS_ORDERED = [
    'Date', 'Time', 'Day', 'Station', 'Code',
    'Min Delay', 'Min Gap', 'Bound', 'Line', 'Vehicle'
]

# Valid bound names:
VALID_BOUND_NAMES = ['N', 'S', 'E', 'W']

# Rush hour

WEEKDAY_RUSH_HOUR = {
    "morning start": time(6, 0),
    "morning end" : time(9, 0),
    "evening start": time(15, 0),
    "evening end": time(19, 0)
}
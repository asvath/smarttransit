import os

# Base directory
BASE_DIR = r'C:\Users\ashaa\OneDrive\Desktop\SmartTransit'
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DOCS_DIR = os.path.join(RAW_DATA_DIR, 'docs')
CODE_DESC_DIR = os.path.join(RAW_DATA_DIR, 'code_descriptions')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

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
import os

from utils.geocode_utils import extract_station_lat_long
from utils.file_utils import write_to_json
from config import RAW_DOCS_DIR

"""
This script extracts the lat long geodata of TTC Subway Stations from OpenStreetMap(OSM) and writes it into
a JSON file. Some stations need to be added manually to the file.
"""

def build_station_geodata():

    data = extract_station_lat_long()
    filepath = os.path.join(RAW_DOCS_DIR, 'ttc_subway_geodata.json')
    write_to_json(filepath, data)

if __name__=="__main__":
   build_station_geodata()
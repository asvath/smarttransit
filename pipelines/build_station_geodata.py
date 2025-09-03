import os

from utils.geocode_utils import extract_station_lat_lon
from utils.file_utils import write_to_json
from config import RAW_DOCS_DIR

"""
This script extracts the lat long geodata of TTC Subway Stations from OpenStreetMap(OSM) and writes it into
a JSON file. Some stations need to be added manually to the file.
"""
stations_to_add = [
    {
        "station name": "Vaughan Metropolitan Centre Station",
        "lat": 43.79417,
        "long": -79.52750
    },
    {
        "station name": "Highway 407 Station",
        "lat": 43.78333,
        "long": -79.52306
    }
]

def build_station_geodata():

    data = extract_station_lat_lon()
    data.extend(stations_to_add)
    data = sorted(data, key=lambda x: x['station name'])
    filepath = os.path.join(RAW_DOCS_DIR, 'ttc_subway_geodata.json')
    write_to_json(filepath, data)

if __name__=="__main__":
   build_station_geodata()
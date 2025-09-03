from typing import Tuple
import osmnx as ox
from config import VALID_STATIONS_FILE
from file_utils import read_txt_to_list

def station_lat_long() -> list:
    """
    Extract station's lat long
    :param name:
    :return:
    """
    station_lat_long_data = []
    valid_stations_list = read_txt_to_list(VALID_STATIONS_FILE)
    # get city boundary
    toronto = ox.geocode_to_gdf("Toronto, Ontario, Canada")

    # get all subway stations inside city boundary
    stations_gdf = ox.features_from_polygon(
        toronto.geometry.iloc[0],
        tags={"station": "subway"}
    ).reset_index()
    # drop any data that has no name
    stations_gdf = stations_gdf.dropna(subset=["name"])

    # drop duplicates
    stations_gdf = stations_gdf.drop_duplicates(subset=["name"], keep="first")

    for _, row in stations_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        pt = geom if geom.geom_type == "Point" else geom.centroid
        name = row["name"]
        if "Station" not in name:
            name += " Station"
        if name in valid_stations_list:
            station_lat_long_data.append(
            {
                "station name": name,
                "lat": pt.x,
                "long": pt.y
            })

    station_lat_long_data = sorted(station_lat_long_data, key=lambda x: x['station name'])
    # verify that lat long has been extracted for all our valid stations, if not we will add them manually
    stations_with_coords = {s["station name"] for s in station_lat_long_data}
    all_names = set(valid_stations_list)

    print("Add data for these stations manually")
    missing = all_names - stations_with_coords
    print(missing)

    return station_lat_long_data
import os.path

from config import EXPORTS_STATS_DIR
from line_stats import generate_all_line_stats
from station_stats import (generate_all_station_stats, check_dataset_complete,
                           generate_all_code_specific_station_stats)
from utils.file_utils import write_to_json
from utils.ttc_loader import TTCLoader

"""
Generates the following stats and saves them in JSON file:
    Generates the following station stats for a given year:
    - total delays
    - time lost measured in days
    - number of major delays (> 20min)
    - % of system-wide delays originating here
    - top reason for delay by count
    - time lost due to top delay by count
    - top reason for delay by time lost
    - time lost due to top delay by time
    
    Generates the following station stats for the lastest year for the leaderboard:
    - total delays
    - time lost measured in days
    - number of major delays (> 20min)
    - % of system-wide delays originating here
    - top reason for delay by count
    - time lost due to top delay by count
    - top reason for delay by time lost
    - time lost due to top delay by time
    
    Generates delay code specific stats for a given range of years:
    - stations that are consistently in top N for a given delay code across the years: 
        - Avg Delay per Incident
        - Avg Count per Year
        - Avg Time Lost per Year
    
    Generates line specific stats:
    -For each line we get stats per bound per time window (e.g Line: YU, Bound: N, Rush Hour: Evening):
        - total number of delays
        - total delay min
        - avg delay min
        - number of days (weekday or weekend)
        - expected no. of delays
        - probability of having at least 1 delay
        - 90th-percentile delay count: smallest k with P(X ≤ k) ≥ 0.90
        - recommended buffer to add to travel time

"""


def generate_stats():
    os.makedirs(EXPORTS_STATS_DIR, exist_ok=True)
    # load data
    loader = TTCLoader()
    df = loader.df
    df["Year"] = df["DateTime"].dt.year

    # generate station stats
    is_complete = check_dataset_complete(df) # check if the latest year is over
    if is_complete:
        year = df["Year"].max()
    else:
        year = df["Year"].max() - 1

    # station stats for the latest complete year
    stations_stats = generate_all_station_stats(df=df,year=year, unit = "hours")
    filepath = os.path.join(EXPORTS_STATS_DIR, 'stations_stats.json')
    write_to_json(filepath, stations_stats)

    # station stats for the latest year (even if the year is incomplete)
    year = df["Year"].max()
    stations_stats_for_leaderboard = generate_all_station_stats(df=df,year=year, unit = "hours")
    filepath = os.path.join(EXPORTS_STATS_DIR, 'leaderboard_stations_stats.json')
    write_to_json(filepath, stations_stats_for_leaderboard)

    # delay code specific stats for the last three years
    code_dict = {"Track Intrusion": ["SUUT", "MUPR1"],"Disorderly Patron" : ["SUDP"], "Fire: Track Level" : ["MUPLB"]}
    code_specific_stats = (
        generate_all_code_specific_station_stats(df, 2023, 2025, code_dict, 10, "hours"))
    filepath = os.path.join(EXPORTS_STATS_DIR, 'code_specific_stats.json')
    write_to_json(filepath, code_specific_stats)

    # line stats for the last three years
    line_stats = generate_all_line_stats(df, 2023, 2025)
    filepath = os.path.join(EXPORTS_STATS_DIR, 'line_stats.json')
    write_to_json(filepath, line_stats)


if __name__=="__main__":
    generate_stats()






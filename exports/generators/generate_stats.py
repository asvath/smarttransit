from utils import file_utils
from station_stats import code_specific_station_stats, generate_all_station_stats, check_dataset_complete
from line_stats import line_stats
from utils.ttc_loader import TTCLoader
"""
Generates the following stats and saves them in JSON file:
    Generates the following station stats for a given year:
    - total delays
    - time lost measured in days
    - number of major delays (> 20min)
    - % of system-wide delays originating here
    - top reason for delay
    
    Generates delay code specific stats for a given range of years:
    - stations that are consistently in top N for a given delay code across the years: 
        - Avg Delay per Incident
        - Avg Count per Year
        - Avg Time Lost per Year (hours)
    
    Generates line specific stats:
    -For each line we get stats per bound per time window (e.g Line: YU, Bound: N, Rush Hour: Evening):
        - total number of delays
        - total delay min
        - avg delay min
        - number of days (weekday or weekend)
        - expected no. of delay
        - probability of having at least 1 delay
        - 90th-percentile delay count: smallest k with P(X ≤ k) ≥ 0.90
        - recommended buffer to add to travel time

"""


def generate_stats():
    loader = TTCLoader()
    df = loader.df
    df["Year"] = df["DateTime"].dt.year

    # generate station stats
    is_complete = check_dataset_complete(df)
    if is_complete:
        year = df["Year"].max()
    else:
        year = df["Year"].max() - 1


    stations_stats = generate_all_station_stats(year,year)


generate_stats()







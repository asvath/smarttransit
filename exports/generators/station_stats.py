import pandas as pd
"""
Generates the following stats based on a given year's data for individual stations:
- total delays
- time lost measured in days
- number of major delays (> 20min)
- % of system-wide delays originating here
- top reason for delay
"""

def station_stats(df_year_station:pd.DataFrame, total_system_wide_delays_year, unit: str = "minutes") ->dict:
    """
    Generates station stats for a given year and station
    :param df_year_station: pd.DataFrame filtered by year and station
    :param total_system_wide_delays_year: total number of system-wide delays for year
    :param unit: units for time lost
    :return: dict containing stats
    """
    # Group by year and sum delays
    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }
    top_delay_category = df_year_station["Delay Category"].value_counts().idxmax()
    top_delay_category_description =df_year_station["Delay Description"].value_counts().idxmax().lower().capitalize()

    # stats
    total_delays = len(df_year_station)
    time_lost = (df_year_station["Min Delay"].sum())/factors[unit]
    number_of_major_delays = len(df_year_station[df_year_station["Min Delay"] >=20])
    percentage_of_delays_orig = (total_delays/total_system_wide_delays_year) * 100
    top_reason_for_delays = f"{top_delay_category}: {top_delay_category_description}"

    return {
        "station_name": df_year_station["Station"].unique()[0],
        "year" : df_year_station["DateTime"].dt.year.unique()[0],
        "total_delays": total_delays,
        f"time_lost_{unit}": round(time_lost, 2),
        "major_delays": number_of_major_delays,
        "pct_of_system_delays_originating": round(percentage_of_delays_orig, 2),
        "top_reason_for_delays": top_reason_for_delays,
    }

def track_intrusion_station_stats(df, code, top_n, unit: str = "minutes"):
    """
    Get the stations that are consistenly in the top N stations with track intrusions and priority one (train is in contact with patron) across different years
    :param df: pd.DataFrame filtered by years (e.g 2023 to 2025)
    :param unit:
    :return:
    """
    # df = df[df["Code"].isin(["SUUT", "MUPR1"])]
    df = df[df["Code"].isin(code)]


    # conversion factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    df["Year"] = df["DateTime"].dt.year
    track_intrusion_stations = (
        df.groupby(["Year", "Station"])
        .size()
        .reset_index(name="Count")
    )

    time_severity = (
        df.groupby(["Station"])["Min Delay"]
        .mean()
        .reset_index(name="Avg Delay per Intrusion")
    )

    time_severity["Avg Delay per Intrusion"] = time_severity["Avg Delay per Intrusion"] / factors[unit]

    count_severity = track_intrusion_stations.groupby(["Station"])["Count"].sum().reset_index(name="Total Count")
    number_of_years = len(df["Year"].unique())
    if number_of_years > 1:
        current_year = df["Year"].max()
        months = df.loc[df["Year"] == current_year, "DateTime"].dt.month.max()
        total_no_of_mths = (number_of_years - 1) * 12 + months

    else:
        total_no_of_mths = number_of_years * 12

    count_severity["Avg Count per Year"] = ((count_severity["Total Count"] / total_no_of_mths) * 12).round(1)

    # take top n stations by year
    top_n_stations_by_year =(
        track_intrusion_stations.sort_values(["Year", "Count"], ascending = [True, False]).
        groupby("Year").head(top_n))

    # Top N stations in a year as a set e.g {Bloor-Yonge, Spadina, St. George}, where year is the index
    station_sets = (
        top_n_stations_by_year.groupby("Year")
                    ["Station"].apply(set)) # e.g 2018



    stations_list_of_sets = station_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    consistent_stations = set.intersection(*stations_list_of_sets)

    if not consistent_stations:
        return []



    consistent_stations_stats = {}
    for s in consistent_stations:
        station_stats = {}
        time_stats = time_severity[time_severity["Station"] == s]
        count_stats = count_severity[count_severity["Station"] == s]

        station_stats["Avg Delay per Intrusion"] = time_stats["Avg Delay per Intrusion"].iloc[0].round(2)
        station_stats["Avg Count per Year"] = count_stats["Avg Count per Year"].iloc[0].round(2)
        station_stats["Avg Time Lost per Year (hours)"] =\
            ((station_stats["Avg Delay per Intrusion"] * station_stats["Avg Count per Year"])
             / factors["hours"]).round(2)
        consistent_stations_stats[s] = station_stats


    return consistent_stations_stats


from utils.ttc_loader import TTCLoader
loader = TTCLoader()

df = loader.filter_selected_years(2023,2025).df
# print(track_intrusion_station_stats(df, ["SUUT", "MUPR1"],10, "minutes"))
print(track_intrusion_station_stats(df, ["SUDP"],10, "minutes"))


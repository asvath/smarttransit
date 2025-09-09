import pandas as pd

def station_stats(df_year_station:pd.DataFrame, total_system_wide_delays_year, unit: str = "minutes") ->dict:
    """
    Generates the following station stats for a given year and station:
    - total delays
    - time lost measured in days
    - number of major delays (> 20min)
    - % of system-wide delays originating here
    - top reason for delay
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

def code_specific_station_stats(df: pd.DataFrame, code:list, code_name:str, top_n:int, unit: str = "minutes"):
    """
    Get the stations that are consistently in the top N stations with a particular delay code
     (e.g disorderly patron) across different years
    :param df: pd.DataFrame filtered by years (e.g. 2023 to 2025)
    :param code: delay code (e.g. SUDP)
    :param top_n: top N stations
    :param unit: units for time lost
    :return: dict containing stats
    """
    code_stats ={}
    df = df.copy()
    df = df[df["Code"].isin(code)]
    df["Year"] = df["DateTime"].dt.year

    # conversion factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    # create dataframe with avg delay per incident per station
    time_severity = (
        df.groupby(["Station"])["Min Delay"]
        .mean()
        .reset_index(name="Avg Delay per Incident")
    )

    # convert units
    time_severity["Avg Delay per Incident"] = time_severity["Avg Delay per Incident"] / factors[unit]

    # create dataframe with number of counts of delay per station by year
    track_intrusion_stations = (
        df.groupby(["Year", "Station"])
        .size()
        .reset_index(name="Count")
    )

    # get the avg count per year
    count_severity = track_intrusion_stations.groupby(["Station"])["Count"].sum().reset_index(name="Total Count")
    total_num_of_mths = num_of_mths(df) # dataframe might not be complete as the latest year may not be over
    count_severity["Avg Count per Year"] = ((count_severity["Total Count"] / total_num_of_mths) * 12).round(1)

    # get top n stations by year
    top_n_stations_by_year =(
        track_intrusion_stations.sort_values(["Year", "Count"], ascending = [True, False]).
        groupby("Year").head(top_n))

    # Top N stations in a year as a set e.g {Bloor-Yonge, Spadina, St. George}, where year is the index
    station_sets = (
        top_n_stations_by_year.groupby("Year")
                    ["Station"].apply(set)) # e.g 2018

    stations_list_of_sets = station_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    # stations that are consistently in the top N across the years
    consistent_stations = set.intersection(*stations_list_of_sets)

    if not consistent_stations:
        return []

    consistent_stations_stats = {}
    for s in consistent_stations:
        station_stats = {}
        time_stats = time_severity[time_severity["Station"] == s]
        count_stats = count_severity[count_severity["Station"] == s]

        station_stats["Avg Delay per Incident"] = time_stats["Avg Delay per Incident"].iloc[0].round(2)
        station_stats["Avg Count per Year"] = count_stats["Avg Count per Year"].iloc[0].round(2)
        station_stats["Avg Time Lost per Year (hours)"] =\
            ((station_stats["Avg Delay per Incident"] * station_stats["Avg Count per Year"])
             / factors["hours"]).round(2)
        consistent_stations_stats[s] = station_stats

    code_stats[code_name] = consistent_stations_stats

    return code_stats

def num_of_mths(df:pd.DataFrame)-> int:
    """
    Gets the total number of months in dataframe
    :param df: pd.DataFrame
    :return: total number of months
    """
    number_of_years = len(df["Year"].unique())
    if number_of_years > 1:
        current_year = df["Year"].max()
        months = df.loc[df["Year"] == current_year, "DateTime"].dt.month.max()

        # if dataset is incomplete (i.e. the most recent year has not ended)
        if months < number_of_years:
            return (number_of_years - 1) * 12 + months

    return number_of_years * 12
import pandas as pd
from config import VALID_STATIONS_FILE, PROCESSED_CODE_DESCRIPTIONS_FILE
from utils import file_utils
from utils.file_utils import read_txt_to_list
from utils.clean_utils import delay_code_category_dict


def generate_station_stats(df_year_station:pd.DataFrame, total_num_system_wide_delays_year, unit: str = "minutes") ->dict:
    """
    Generates the following station stats for given year and station:
    - total delays
    - time lost measured in days
    - number of major delays (> 20min)
    - % of system-wide delays originating here
    - top reason for delay by count
    - time lost due to top delay by count
    - top reason for delay by time
    - time lost due to top delay by time
    :param df_year_station: pd.DataFrame filtered by year and station
    :param total_num_system_wide_delays_year: total number of system-wide delays for year
    :param unit: units for time lost
    :return: dict containing stats
    """
    station_stats = {}
    # Group by year and sum delays
    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    #
    delay = (
        df_year_station.groupby("Code")["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
        .sort_values("Total Delay", ascending= False)
    )
    # delay code: public explanation dict
    delay_code_public_explanation = delay_code_public_explanation_dict()
    # delay code: category dict
    delay_code_category = delay_code_category_dict()

    # top delay by count
    top_delay_code = df_year_station["Code"].value_counts().idxmax() # by count
    top_delay_public_explanation  = delay_code_public_explanation[top_delay_code]
    top_delay_category = delay_code_category[top_delay_code]
    time_lost_due_to_delay = delay[delay["Code"]==top_delay_code]["Total Delay"].iloc[0]


    # top delay by time lost
    top_time_delay_code = delay.iloc[0]["Code"]
    top_time_delay_public_explanation = delay_code_public_explanation[top_time_delay_code]
    top_time_delay_category = delay_code_category[top_time_delay_code]
    time_lost_due_to_top_time_delay = delay.iloc[0]["Total Delay"]


    # stats
    total_delays = len(df_year_station)
    time_lost = (df_year_station["Min Delay"].sum())/factors[unit]
    number_of_major_delays = len(df_year_station[df_year_station["Min Delay"] >=20])
    percentage_of_delays_orig = (total_delays/total_num_system_wide_delays_year) * 100
    top_reason_for_delays = f"{top_delay_category}: {top_delay_public_explanation}"
    time_lost_due_to_top_delay_by_count = round(time_lost_due_to_delay/factors[unit],2)
    top_reason_for_delays_by_time = f"{top_time_delay_category}: {top_time_delay_public_explanation}"
    time_lost_due_to_top_delay_by_time = round(time_lost_due_to_top_time_delay/factors[unit], 2)
    year = df_year_station["DateTime"].dt.year.unique().tolist()


    station_stats[df_year_station["Station"].unique()[0]] = {
        "year": year,
        "total_delays": int(total_delays),
        f"time_lost_{unit}": float(round(time_lost, 2)),
        "major_delays": int(number_of_major_delays),
        "pct_of_system_delays_originating": float(round(percentage_of_delays_orig, 2)),
        "top_reason_for_delays (by count)": top_reason_for_delays,
        "time_lost_due_to_top_delay_by_count" : float(time_lost_due_to_top_delay_by_count),
        "top_reason_for_delays_by_time": top_reason_for_delays_by_time,
        "time_lost_due_to_top_delay_by_time": float(time_lost_due_to_top_delay_by_time)
    }

    return station_stats

def generate_all_station_stats(df:pd.DataFrame, year:int, unit:str = "minutes") ->dict:
    """
    Generates stats for all stations for given years
    :param df: pd.DataFrame
    :param year: year
    :param unit: units for time lost
    :return: dict containing stats for all stations
    """
    valid_stations_list = read_txt_to_list(VALID_STATIONS_FILE)
    df_year = df[df["Year"]==year]
    total_num_of_system_wide_delays = len(df_year)

    stations_stats_list = []
    for station in valid_stations_list:
        df_station = df_year[df_year["Station"] == station.upper()]
        station_stats = generate_station_stats(df_station, total_num_of_system_wide_delays, unit)
        stations_stats_list.append(station_stats)

    return {"stations_stats": stations_stats_list}


def code_specific_station_stats(df: pd.DataFrame, year_start:int, year_end:int, code:list, code_name:str, top_n:int, unit: str = "minutes") -> dict:
    """
    Get the stats of stations that are consistently in the top N stations with a particular delay code
     (e.g disorderly patron) across different years
    :param df: pd.DataFrame filtered by years (e.g. 2023 to 2025)
    :param year_start: start year
    :param year_end: end year
    :param code: delay code (e.g. SUDP)
    :param code_name: user-defined name of delay code, (e.g. Disorderly Patron)
    :param top_n: top N stations
    :param unit: units for time lost
    :return: dict containing stats
    """
    code_stats ={}
    df = df.copy()
    df = df[df["Year"].isin([year_start, year_end])]
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

    # Top N stations in a year as a set
    # e.g. 2018: (Bloor-Yonge, Spadina, St. George), 2019: (Bloor-Yonge, Rosedale), where year is the index
    station_sets = (
        top_n_stations_by_year.groupby("Year")
                    ["Station"].apply(set))

    stations_list_of_sets = station_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    # stations that are consistently in the top N across the years
    consistent_stations = set.intersection(*stations_list_of_sets)

    if not consistent_stations:
        return {}

    consistent_stations_stats = {}
    for s in consistent_stations:
        station_stats = {}
        time_stats = time_severity[time_severity["Station"] == s]
        count_stats = count_severity[count_severity["Station"] == s]

        station_stats["Avg Delay per Incident"] = time_stats["Avg Delay per Incident"].iloc[0].round(2)
        station_stats["Avg Count per Year"] = count_stats["Avg Count per Year"].iloc[0].round(2)
        station_stats[f"Avg Time Lost per Year ({unit})"] =\
            ((station_stats["Avg Delay per Incident"] * station_stats["Avg Count per Year"])
             / factors[unit]).round(2)
        station_stats["Year"] = f"{year_start} - {year_end}"
        consistent_stations_stats[s] = station_stats

    code_stats[code_name] = consistent_stations_stats

    return code_stats

def num_of_mths(df:pd.DataFrame)-> int:
    """
    Gets the total number of months in dataframe
    :param df: pd.DataFrame
    :return: total number of months
    """
    return df["DateTime"].dt.to_period("M").nunique()

def check_dataset_complete(df:pd.DataFrame) -> bool:
    """
    check if dataset is complete as the latest year may not be over
    :param df: pd.DataFrame
    :return: bool
    """
    latest_year = df["Year"].max()
    months = df.loc[df["Year"] == latest_year, "DateTime"].dt.month.max()
    return months == 12

def delay_code_public_explanation_dict() -> dict:
    """
    Creates a dictionary mapping delay codes public friendly explanation. e.g SUDP: Disorderly Patron
    """
    df = file_utils.read_csv(PROCESSED_CODE_DESCRIPTIONS_FILE)
    return dict(zip(df["CODE"], df["PUBLIC EXPLANATION"]))
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

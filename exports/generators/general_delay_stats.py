import pandas as pd
from config import VALID_UNITS, CONVERSION_FACTORS

def generate_general_delay_stats(df:pd.DataFrame, year_start: int, year_end: int,
                                 delay_code: list= None, unit: str = "minutes") ->dict:
    """
    Generates the following delay statistics:
    - Average delay time
    - Median delay time
    - Delays per year
    - Delays per month
    - Delays per day
    - Standard deviation of delay time
    - 90th percentile delay time
    - Delay code or "General" if not specified

    :param df: pd.DataFrame filtered by year and station
    :param year_start: start year for analysis
    :param year_end: end year for analysis
    :param delay_code: delay code
    :param unit: units for time lost
    :return: dict containing stats
    """

    # Calculate delay summary statistics
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversion factor
    factors = CONVERSION_FACTORS

    df = df[df['DateTime'].dt.year.between(year_start, year_end)].copy()

    # Filter by delay code if specified
    if delay_code:
        df = df[df['Code'].isin(delay_code)].copy()

    no_of_years = df["DateTime"].dt.year.nunique()
    num_days = df["DateTime"].dt.date.nunique()
    num_months = df["DateTime"].dt.to_period('M').nunique()

    # Calculate values with conversion applied
    avg_delay_time = df["Min Delay"].mean() / factors[unit]
    avg_delay_count = df["Min Delay"].count() / no_of_years
    median_delay_time = df["Min Delay"].median() / factors[unit]
    delays_per_mth =  df["Min Delay"].count() / num_months
    delays_per_day = df["Min Delay"].count() / num_days
    delay_time_std = df["Min Delay"].std()/ factors[unit]
    ninetieth_percentile= df["Min Delay"].quantile(0.90)/ factors[unit]


    delay_summary = {
        'Delay Code': delay_code if delay_code else "General",
        f'Average Delay Time ({unit})': avg_delay_time,
        f'Median Delay Time ({unit})': median_delay_time,
        'Delays per Year': avg_delay_count,
        'Delays per Month': delays_per_mth,
        'Delays per Day': delays_per_day,
        f'Std Deviation Time ({unit})': delay_time_std,
        f'90th Percentile ({unit})': ninetieth_percentile,
        'Years' : f" {year_start} - {year_end}",


    }

    return delay_summary

def generate_code_specific_general_delay_stats(df: pd.DataFrame, year_start: int, year_end: int,
                                             code_dict: dict, unit: str = "minutes") -> dict:
    """
     For each delay code in given dict, generates the following delay statistics:
    - Average delay time
    - Median delay time
    - Delays per year
    - Delays per month
    - Delays per day
    - Standard deviation of delay time
    - 90th percentile delay time
    - Delay code
    :param df: pd.DataFrame
    :param year_start: start year for analysis
    :param year_end: end year  for analysis
    :param code_dict: mapping of user-specified code name to TTC specified delay code (e.g. "Disorderly Patron": "SUDP")
    :param unit: output time unit
    :return: dict containing stats for each delay code
    """
    code_stats = []
    for code_name, code in code_dict.items():
        stats = generate_general_delay_stats(df, year_start, year_end, code, unit)
        stats['Code Name'] = code_name  # Add the user-friendly name
        code_stats.append(stats)
    return {"Code Specific General Delay Stats" : code_stats}
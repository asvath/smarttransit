import pandas as pd
from config import VALID_UNITS, CONVERSION_FACTORS

def generate_general_delay_stats(df:pd.DataFrame, delay_code: str = None, unit: str = "minutes") ->dict:
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
    :param delay_code: delay code
    :param unit: units for time lost
    :return: dict containing stats
    """

    # Calculate delay summary statistics
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversion factor
    factors = CONVERSION_FACTORS

    no_of_years = df["DateTime"].dt.year.unique().shape[0]
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
        f'Average Delay Time ({unit})': avg_delay_time,
        f'Median Delay Time ({unit})': median_delay_time,
        'Delays per Year': avg_delay_count,
        'Delays per Month': delays_per_mth,
        'Delays per Day': delays_per_day,
        f'Std Deviation Time ({unit})': delay_time_std,
        f'90th Percentile ({unit})': ninetieth_percentile,
        'Delay Code': delay_code if delay_code else "General"

    }

    return delay_summary


import pandas as pd
from config import VALID_LINECODES_TO_BOUND_DICT
from scipy.stats import poisson

def solve_for_k(lmbda, p=0.9):
    """
    Find the smallest k such that P(X <= k) >= p
    for X ~ Poisson(lmbda).
    """
    k = 0
    while poisson.cdf(k, lmbda) < p:
        k += 1
    return k

def round_to_nearest_5(x):
    """Round number to nearest 5"""
    return int(round(x / 5.0)) * 5

WEEKEND_SERVICE_HOURS = 19   # avg span across Sat (~20h) & Sun (~18h)
WEEKEND_EXPOSURE_HOURS = 5   # chosen comparable to weekday exposure window

def freq_of_delays(row) -> float:
    """
    Compute lambda (expected number of delay events) for this time bucket.
    :param row : pd.Series containing "Rush Hour", "number_of_delays", "days_in_dataset"
    :return expected no. of delays in a time bucket.
    Rationale:
    - Weekday buckets (Morning / Off-peak: Afternoon / Evening / Off-peak: Night)
      already count delays within that specific 3–7h window. Dividing total delays per bucket by the number
      of weekdays in the dataframe gives delays on weekday per bucket

    - Weekend rows aggregate the entire service day (~19h on average across Sat/Sun).
      To make that comparable to weekday analysis, convert to an hourly rate
      and scale to a 5-hour slice:
          (delays per weekend day ÷ 19 hours) × 5 hours.
      This yields a λ for a 5-hour weekend window instead of the whole day.
    """
    if row["Rush Hour"] == "Weekend":
        # Normalize weekend “per day” to a 5-hour slice:
        #   delays_per_day   = number_of_delays / (weekend) days_in_dataset
        #   delays_per_hour  = delays_per_day / 19    (avg weekend service span)
        #   lambda_for_5hrs  = delays_per_hour * 5
        return ((row["number_of_delays"] / row["days_in_dataset"]) / 19) * 5

    # Weekday windows: number_of_delays already refers to that bucket only.
    # So λ = delays_in_window_per_day (i.e., per weekday with data).
    return row["number_of_delays"] / row["days_in_dataset"]

def line_stats(df_year_line:pd.DataFrame,line_name: str) ->dict | None:
    """
    Generates the following stats individual lines for given years e.g 2023-2025:
    - For each line we get stats per bound per time window (e.g Line: YU, Bound: N, Rush Hour: Evening):
        - total number of delays
        - total delay min
        - avg delay min
        - number of days (weekday or weekend)
        - expected no. of delay
        - probability of having at least 1 delay
        - 90th-percentile delay count: smallest k with P(X ≤ k) ≥ 0.90
        - recommended buffer to add to travel time
    :param df_year_line: pd.DataFrame filtered by line and years (e.g "YU" from 2023-2025)
    :param line_name: name of line, e.g ("YU"
    :return: dict containing stats
    """
    results = {}

    # bound-specific stats
    bound_stats = {}
    bounds = VALID_LINECODES_TO_BOUND_DICT[line_name]

    for b in bounds:
        df_bound = df_year_line[df_year_line["Bound"] == b]

        rush_stats = (
            df_bound.groupby("Rush Hour")["Min Delay"]
            .agg(
                number_of_delays="count",
                total_delay_minutes="sum",
                avg_delay_minutes="median" # median to account for major delays
            )
            .reset_index()
        )

        rush_stats["bound"] = b
        rush_stats["total_delay_minutes"] = rush_stats["total_delay_minutes"].round(2)
        rush_stats["avg_delay_minutes"] = rush_stats["avg_delay_minutes"].round(2)

        # number of weekdays and weekends in our dataframe
        num_weekdays = df_bound.loc[df_bound["IsWeekday"], "DateTime"].dt.date.nunique()
        num_weekends = df_bound.loc[~df_bound["IsWeekday"], "DateTime"].dt.date.nunique()

        def pick_days(row):
            return num_weekends if row["Rush Hour"] == "Weekend" else num_weekdays

        # add column that shows the number of days for that rush hour time frame
        # e.g Morning: 500 days, weekends 200 days
        rush_stats["days_in_dataset"] = rush_stats.apply(pick_days, axis=1)

        # lambda for this time window: expected number of delay events (Poisson rate)
        rush_stats["expected_delays"] = rush_stats.apply(freq_of_delays,axis = 1)

        # Chance your trip encounters at least one delay in this time window: P(X ≥ 1) for X~Poisson(λ)
        rush_stats["p_any_delay"] = (
                1 - poisson.pmf(0, rush_stats["expected_delays"])
        ).round(3)

        # 90th-percentile delay count: smallest k with P(X ≤ k) ≥ 0.90
        # (i.e., only 10% of trips would have more than k delays)
        rush_stats["k_at_90pct"] = rush_stats["expected_delays"].apply(solve_for_k)

        # Recommended padding: typical single-delay minutes × p90 delay count
        rush_stats["recommended_buffer_min"] = rush_stats["avg_delay_minutes"] * rush_stats["k_at_90pct"]

        # Round the recommended padding to nearest 5 min
        rush_stats["recommended_buffer_min"] = rush_stats["recommended_buffer_min"].apply(round_to_nearest_5)

        bound_stats[b] = rush_stats.to_dict(orient="records")

    results[line_name] = bound_stats

    return results
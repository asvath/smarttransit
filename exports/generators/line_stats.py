import pandas as pd
from config import VALID_LINECODES_TO_BOUND_DICT
from scipy.stats import poisson
"""
Generates the following stats based on a given year's data for individual lines:
- total delays
- time lost measured in days
- number of major delays (> 20min)
- % of system-wide delays originating here
- top reason for delay
"""

def line_stats(df_year_line:pd.DataFrame,line_name: str) ->dict | None:
    """
    Generates station stats for a given year and station
    :param df_year_line: pd.DataFrame filtered by year and station
    :return: dict containing stats
    """
    results = {}
    time_windows = {
        "Morning": 3,  # 6–9am
        "Off-peak: Afternoon": 6,  # 9am–3pm
        "Evening": 3,  # 4–7pm
        "Off-peak: Night": 7,  # 7pm–2am
        "Weekend": 20  # adjust if needed
    }

    # bound-specific stats
    bound_stats = []
    bounds = VALID_LINECODES_TO_BOUND_DICT[line_name]

    for b in bounds:
        df_bound = df_year_line[df_year_line["Bound"] == b]

        rush_stats = (
            df_bound.groupby("Rush Hour")["Min Delay"]
            .agg(
                number_of_delays="count",
                total_delay_minutes="sum",
                avg_delay_minutes="median"
            )
            .reset_index()
        )

        num_weekdays = df_bound.loc[df_bound["IsWeekday"], "DateTime"].dt.date.nunique()
        num_weekends = df_bound.loc[~df_bound["IsWeekday"], "DateTime"].dt.date.nunique()

        rush_stats["bound"] = b
        rush_stats["total_delay_minutes"] = rush_stats["total_delay_minutes"].round(2)
        rush_stats["avg_delay_minutes"] = rush_stats["avg_delay_minutes"].round(2)
        rush_stats["hours_in_window"] = rush_stats["Rush Hour"].map(time_windows)

        def pick_days(row):
            return num_weekends if row["Rush Hour"] == "Weekend" else num_weekdays

        rush_stats["days_in_dataset"] = rush_stats.apply(pick_days, axis=1)

        rush_stats["frequency_of_delays"] = (
            rush_stats["number_of_delays"] /rush_stats["days_in_dataset"]
        ).round(2)

        # probability of experience at least 1 delay during commute:
        rush_stats["probability_of_delay"] = (
                1 - poisson.pmf(0, rush_stats["frequency_of_delays"])
        ).round(3)

        bound_stats.append(rush_stats.to_dict(orient="records"))

    results[line_name] = bound_stats
    return results


from utils.ttc_loader import TTCLoader
loader = TTCLoader()

df_year_line = loader.filter_selected_years(2023,2025).filter_line("YU").df
print(line_stats(df_year_line, "YU"))
line_stats(df_year_line, "YU")
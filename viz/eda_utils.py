import pandas as pd

def get_consistently_top_stations(df: pd.DataFrame, top_n: int = 10, last_n_years: int = None)-> list:
    """
    Get stations that repeatedly rank in the top-N for total delay across the last n years.
    :param df: pd.DataFrame
    :param top_n: top n stations
    :param last_n_years: last n years to analyze, if none, all years
    :return: list of stations that repeatedly rank in the top-N for total delay across the last n years
    """
    df = df.copy()
    df["Year"] = df["DateTime"].dt.year

    # If user specified how many recent years to include
    if last_n_years is not None:
        all_years_sorted = sorted(df["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df = df[df["Year"].isin(selected_years)]

    # Get total delay per year

    yearly = (
        df.groupby(["Year","Station"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    # Get top-n stations per year

    top_n_stations_by_year =(
        yearly.sort_values(["Year","Total Delay"], ascending = [True, False])
        .groupby(yearly["Year"]).
        head(top_n)
    )

    # Find stations that are in the top-N across all years
    station_sets = (
        top_n_stations_by_year.groupby("Year")
                    ["Station"].apply(set)) # e.g 2018    {Bloor-Yonge, Spadina, St. George}, where year is the index

    stations_list_of_sets = station_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    consistent_stations = set.intersection(*stations_list_of_sets)

    if not consistent_stations:
        return []

    return list(consistent_stations)
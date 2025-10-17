from pydoc import html

import pandas as pd

import plotly.graph_objects as go



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

def get_consistently_top_vehicles(df: pd.DataFrame, top_n: int = 10, last_n_years: int = None)-> list:
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
        df.groupby(["Year","Vehicle"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    # Get top-n stations per year

    top_n_vehicles_by_year =(
        yearly.sort_values(["Year","Total Delay"], ascending = [True, False])
        .groupby(yearly["Year"]).
        head(top_n)
    )

    # Find stations that are in the top-N across all years
    vehicle_sets = (
        top_n_vehicles_by_year.groupby("Year")
                    ["Vehicle"].apply(set)) # e.g 2018    {Bloor-Yonge, Spadina, St. George}, where year is the index

    stations_list_of_sets = vehicle_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    vehicle_stations = set.intersection(*stations_list_of_sets)

    if not vehicle_stations:
        return []

    return list(vehicle_stations)

def get_top_stations_w_track_intrusions(df, top_n = 5, last_n_years = None):
    df = df.copy()
    df["Year"] = df["DateTime"].dt.year

    # If user specified how many recent years to include
    if last_n_years is not None:
        all_years_sorted = sorted(df["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df = df[df["Year"].isin(selected_years)]

    # Get only track intrusions
    df = df[df["Code"] == "SUUT"]
    # df = df[df["Delay Category"] == "Patron"]

    # Get total delay per year

    yearly = (
        df.groupby(["Year","Station"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    print(yearly["Year"].unique())
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

    print(station_sets)

    stations_list_of_sets = station_sets.tolist() # e.g [{Bloor-Yonge, Spadina}, {Bloor-Yonge, Rosedale}]

    consistent_stations = set.intersection(*stations_list_of_sets)

    if not consistent_stations:
        return []

    return list(consistent_stations)

def fig_to_html(fig:go.Figure, filepath:str, title:str)->None:
    fig.update_layout(autosize=True, width=None, height=None)
    fig.write_html(
        f"{filepath}/{title}.html",
        include_plotlyjs="cdn",  # loads Plotly from CDN (keeps file small)
        full_html=True,  # standalone file
        config={
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]
        }
    )

if __name__ == "__main__":
    from viz.eda_plots import plot_total_delay_by_year
    from utils.ttc_loader import TTCLoader

    loader = TTCLoader()
    df = loader.df
    fig = plot_total_delay_by_year(df, "days")
    fig_to_html(fig, r"C:\Users\ashaa\OneDrive\Desktop\SmartTransit\exports\plots", "total_delay_by_year")
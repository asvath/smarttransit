import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from eda_utils import get_consistently_top_stations


def plot_total_delay_by_year(df:pd.DataFrame, unit: str = "minutes", graphtype: str = "bar") -> go.Figure:
    """
    Plots the total delay in given units (min, hours, days) by year
    :param df: pd.Dataframe of TTC delays
    :param unit: measurement of the delay in minutes, hours or days
    :return: plot
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

    yearly = (
        df.groupby(df["DateTime"].dt.year)["Min Delay"]
          .sum()
          .reset_index(name="Total Delay")
    )


    # latest year & month in dataset
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # apply conversion
    yearly["Total Delay"] = yearly["Total Delay"] / factors[unit]

    if graphtype == "bar":
        fig = px.bar(
            yearly,
            x="DateTime",
            y="Total Delay",
            title=f"Total TTC Delay Measured in {unit.capitalize()} Lost by Year",
            labels={ "DateTime": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
        )
    else:
        fig = px.line(
            yearly,
            x="DateTime",
            y="Total Delay",
            title=f"Total TTC Delay Measured in {unit.capitalize()} Lost by Year",
            labels={ "DateTime": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
        )


    latest_value =\
        yearly.loc[yearly["DateTime"] == latest_year, "Total Delay"].item()# Total Delay in the latest year
    fig.add_annotation(
        x=latest_year,
        y=latest_value,
        text=f"till {latest_month} {latest_year}",
        showarrow=False,
        yshift=10,  # move label a little above the bar
        font=dict(color="black", size=12)
    )

    fig.add_annotation(
        x=2020,
        y=yearly.loc[yearly["DateTime"] == 2020, "Total Delay"].item(),
        text=f"COVID-19",
        showarrow=False,
        yshift=10,  # move label a little above the bar
        font=dict(color="black", size=12)
    )

    return fig

def plot_delay_category_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
    """
    Plot top-N delay category trends across all years
    :param df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n delay categories (e.g Patrons, Mechanical/Infrastructure)
    :return: plot
    """
    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    yearly_cat = (
        df
        .groupby([df["DateTime"].dt.year.rename("Year"), "Delay Category"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    yearly_cat["Total Delay"] = yearly_cat["Total Delay"] / factors[unit]

    top_n_cat =(
        yearly_cat.sort_values(["Year", "Total Delay"], ascending = [True, False]) # sort rows by year and total delay
        .groupby(yearly_cat["Year"]).head(top_n)
    )


    fig = px.bar(
        top_n_cat,
        x="Year",
        y="Total Delay",
        color= "Delay Category",
        barmode="group",
        title=f"TTC Delay by Category over Time measured in {unit.capitalize()} Lost by Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
    )

    fig = fig.for_each_xaxis(lambda ax: ax.update(categoryorder="total descending"))
    return fig

def plot_delay_description_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
    """
    Plot top-N delay category trends across all years
    :param df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n delay categories (e.g Patrons, Mechanical/Infrastructure)
    :return: plot
    """
    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    yearly_cat = (
        df
        .groupby([df["DateTime"].dt.year.rename("Year"), "Delay Description"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    yearly_cat["Total Delay"] = yearly_cat["Total Delay"] / factors[unit]

    top_n_cat =(
        yearly_cat.sort_values(["Year", "Total Delay"], ascending = [True, False]) # sort rows by year and total delay
        .groupby(yearly_cat["Year"]).head(top_n)
    )

    years = top_n_cat["Year"].unique()
    categories = top_n_cat["Delay Description"].unique()
    full_index = pd.MultiIndex.from_product([years, categories], names=["Year", "Delay Description"])

    top_n_cat = (
        top_n_cat.set_index(["Year", "Delay Description"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    fig = px.bar(
        top_n_cat,
        x="Year",
        y="Total Delay",
        color= "Delay Description",
        barmode="group",
        title=f"TTC Delay by Category over Time measured in {unit.capitalize()} Lost by Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
    )

    fig = fig.for_each_xaxis(lambda ax: ax.update(categoryorder="total descending"))
    return fig

def plot_station_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
    """
    Plot the top n stations with delays by year
    :param df: pd.DataFrame of TTC delay
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n categories of delay
    :return:
    """
    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    yearly_cat = (
        df
        .groupby([df["DateTime"].dt.year.rename("Year"), "Station"])["Min Delay"]
        .sum()
        .reset_index(name="Total Delay")
    )

    yearly_cat["Total Delay"] = yearly_cat["Total Delay"] / factors[unit]

    # take top n stations of delay per year
    top_n_cat =(
        yearly_cat.sort_values(["Year", "Total Delay"], ascending = [True, False]) # sort rows by year and total delay
        .groupby(yearly_cat["Year"]).head(top_n)
    )

    fig = px.bar(
        top_n_cat,
        x="Year",
        y="Total Delay",
        barmode="group",
        color= "Station",
        title=f"TTC Delays Over Time: Top {top_n} stations by {unit.capitalize()} Lost per Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} lost"}
    )

    return fig



def plot_consistently_top_station_trend(df, unit: str = "minutes", top_n: int = 5, last_n_years: int = None) -> go.Figure:
    """Line graph showing delay trends over the years, of the stations that are consistently ranked in the
    top-N stations with delays
    df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: Ranked top-N stations
    :param last_n_years: last n years to analyze, if none, all years
    :return line graph
    """
    # latest year & month in dataset, as the dataset might not be complete (e.g till May 2025)
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # get stations that are consistently in the top-N stations for the last N years
    consistently_top_stations = get_consistently_top_stations(df, top_n, last_n_years)

    # filter dataframe for stations that are consistently in the top-N stations
    df_filtered = df[df["Station"].isin(consistently_top_stations)].copy()
    # filter dataframe for last N years
    df_filtered.loc[:, "Year"] = df_filtered["DateTime"].dt.year
    if last_n_years is not None:
        all_years_sorted = sorted(df_filtered["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df_filtered = df_filtered[df_filtered["Year"].isin(selected_years)]


    if unit not in {"minutes", "hours", "days"}:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = {
        "minutes": 1,
        "hours": 60,
        "days": 60 * 24,
    }

    yearly = (
        df_filtered.groupby(["Year", "Station"])["Min Delay"]
        .sum()
        .reset_index(name = "Total Delay")
    )

    yearly["Total Delay"] = yearly["Total Delay"] / factors[unit]

    fig = px.bar(
        yearly,
        x="Year",
        y="Total Delay",
        color="Station",
        barmode = "group",
        title=f"TTC Delays Over Time: Stations that are consistently in the Top {top_n} stations by {unit.capitalize()} Lost per Year",
        labels={
            "Year": "Year",
            "Total Delay": f"Total Delay ({unit})",
            "Station": "Station"
        }
    )

    # add annotation if the dataset is not complete (e.g till May 2025)
    if latest_month != "December":

        biggest_delay_in_latest_year = yearly[yearly['Year'] == latest_year]['Total Delay'].max()

        fig.add_annotation(
            x=latest_year,
            y=biggest_delay_in_latest_year,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift=10,  # move label a little above the bar
            font=dict(color="black", size=12)
        )
    return fig



### Spatial and Temporal Patterns
# Which subway lines are most delay-prone
def plot_line_trends_by_year(df:pd.DataFrame, unit: str = "minutes") -> go.Figure:
    """
    Plots the total delay in given units (min, hours, days) by year across the Lines (YU, BD, SHP)
    :param df: pd.Dataframe of TTC delays
    :param unit: measurement of the delay in minutes, hours or days
    :return: plot
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

    yearly = (
        df.groupby([df["DateTime"].dt.year, "Line"])["Min Delay"]
          .sum()
          .reset_index(name="Total Delay")
    )


    # latest year & month in dataset
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # apply conversion
    yearly["Total Delay"] = yearly["Total Delay"] / factors[unit]

    # plot bar graph
    fig = px.bar(
        yearly,
        x="DateTime",
        y="Total Delay",
        color= "Line",
        barmode= "group",
        title=f"TTC Delays Over Time: Yearly {unit.capitalize()} Lost Across Lines",
        labels={ "DateTime": "Year", "Total Delay": f"{unit.capitalize()} Lost"},
        color_discrete_map={
            "YU": "goldenrod",   # Yonge–University
            "BD": "green",    # Bloor–Danforth
            "SHP": "red"      # Sheppard
        },
        category_orders={"Line": ["BD", "YU", "SHP"]}  # forces order
    )

    # Add trend, linegraph
    # Map Year + small offset per line for the x-coordinate on the plot
    offsets = {"BD": -0.25, "YU": 0, "SHP": 0.25}
    yearly["Year_offset"] = yearly["DateTime"] + yearly["Line"].map(offsets)
    for line in ["BD", "YU", "SHP"]:
        line_data = yearly[yearly["Line"] == line]
        fig.add_scatter(
            x=line_data["Year_offset"],  # shifted per line
            y=line_data["Total Delay"],
            mode="lines+markers",
            name=f"{line} Trend",
            line=dict(dash="dot")
        )

    # add annotation if dataset is not complete (e.g. till May 2025)
    if latest_month != "December":
        latest_value =\
            yearly.loc[yearly["DateTime"] == latest_year, "Total Delay"].max()# Total Delay in the latest year
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift=20,  # move label a little above the bar
            font=dict(color="black", size=12)
        )

    # Add covid annotation
    fig.add_annotation(
        x=2020,
        y=yearly.loc[yearly["DateTime"] == 2020, "Total Delay"].max(),
        text=f"COVID-19",
        showarrow=False,
        yshift=20,  # move label a little above the bar
        font=dict(color="black", size=12)
    )

    return fig

# When do delays occur most often - during peak or off-peak hours
def plot_rush_hour_trends_by_year(df:pd.DataFrame, unit: str = "minutes") -> go.Figure:
    """
    Plots the total delay in given units (min, hours, days) by year across the Lines (YU, BD, SHP)
    :param df: pd.Dataframe of TTC delays
    :param unit: measurement of the delay in minutes, hours or days
    :return: plot
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

    df["Year"] = df["DateTime"].dt.year
    rush = (
        df.groupby(["Year", "Rush Hour"], as_index=False)
        .agg(
            Delays=("Min Delay", "count"),  # number of delay events
            TotalMinutes=("Min Delay", "sum")  # total delay time in minutes (sum of Min Delay)
        )
        .rename(columns={"DateTime": "Year"})
    )

    # latest year & month in dataset
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # apply conversion
    rush["Total Delay"] = rush["TotalMinutes"] / factors[unit]

    label_map = {
        "Morning": "Morning: 6am – 9am",
        "Evening": "Evening: 3pm – 7pm",
        "Off-peak: Afternoon": "Off-Peak: Weekday 9am - 3pm",
        "Off-peak: Night" : "Off-peak: Weekday 7pm - 2am",
        "Weekend": "Weekend"
    }
    rush["Rush Hour"] = rush["Rush Hour"].replace(label_map)

    fig = px.bar(
        rush,
        x="Year",
        y="Total Delay",
        color="Rush Hour",
        barmode="group",
        title=f"TTC Delays Over Time: Yearly {unit.capitalize()} Lost During Peak vs Off-Peak",
        labels={ "Total Delay": f"{unit.capitalize()} Lost"},
        category_orders = {"Rush Hour": ["Morning: 6am – 9am", "Off-Peak: Weekday 9am - 3pm",
                                         "Evening: 3pm – 7pm", "Off-peak: Weekday 7pm - 2am", "Weekend"]}  # forces order
    )

    # add annotation if dataset is not complete (e.g. till May 2025)
    if latest_month != "December":
        latest_value =\
            rush.loc[rush["Year"] == latest_year, "Total Delay"].max()# Total Delay in the latest year
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift=20,  # move label a little above the bar
            font=dict(color="black", size=12)
        )

    # Add covid annotation
    fig.add_annotation(
        x=2020,
        y=rush.loc[rush["Year"] == 2020, "Total Delay"].max(),
        text=f"COVID-19",
        showarrow=False,
        yshift=20,  # move label a little above the bar
        font=dict(color="black", size=12)
    )

    return fig

# Which season has the most delays
def plot_season_trends_by_year(df:pd.DataFrame, unit: str = "minutes") -> go.Figure:
    """
    Plots the total delay in given units (min, hours, days) by year across the Lines (YU, BD, SHP)
    :param df: pd.Dataframe of TTC delays
    :param unit: measurement of the delay in minutes, hours or days
    :return: plot
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

    df["Year"] = df["DateTime"].dt.year
    season = (
        df.groupby(["Year", "Season"], as_index=False)
        .agg(
            Delays=("Min Delay", "count"),  # number of delay events
            TotalMinutes=("Min Delay", "sum")  # total delay time in minutes (sum of Min Delay)
        )
        .rename(columns={"DateTime": "Year"})
    )

    # latest year & month in dataset
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # apply conversion
    season["Total Delay"] = season["TotalMinutes"] / factors[unit]
    # Mapping season to month
    label_map = {
        "Winter": "Winter: Dec - Feb",
        "Spring": "Spring: Mar - May",
        "Summer": "Summer: Jun - Aug",
        "Fall": "Fall; Sep - Nov"
    }
    season["Season"] = season["Season"].replace(label_map)

    fig = px.bar(
        season,
        x="Year",
        y="Total Delay",
        color="Season",
        barmode="group",
        title=f"TTC Delays Over Time: Yearly {unit.capitalize()} Lost Across the Seasons",
        labels={ "Total Delay": f"{unit.capitalize()} Lost"},
        color_discrete_map={
            "Winter: Dec - Feb": "navy",
            "Spring: Mar - May": "forestgreen",
            "Summer: Jun - Aug": "gold",
            "Fall: Sep - Nov": "darkorange"
        },
        category_orders = {"Season": ["Winter: Dec - Feb", "Spring: Mar - May", "Summer: Jun - Aug", "Fall; Sep - Nov" ]}  # forces order
    )

    # add annotation if dataset is not complete (e.g. till May 2025)
    if latest_month != "December":
        latest_value =\
            season.loc[season["Year"] == latest_year, "Total Delay"].max()# Total Delay in the latest year
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift=20,  # move label a little above the bar
            font=dict(color="black", size=12)
        )

    # Add covid annotation
    fig.add_annotation(
        x=2020,
        y=season.loc[season["Year"] == 2020, "Total Delay"].max(),
        text=f"COVID-19",
        showarrow=False,
        yshift=20,  # move label a little above the bar
        font=dict(color="black", size=12)
    )

    return fig

def plot_histogram_delay_duration(df, last_n_years: int = None) -> go.Figure:
    """Line graph showing delay trends over the years, of the stations that are consistently ranked in the
    top-N stations with delays
    df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: Ranked top-N stations
    :param last_n_years: last n years to analyze, if none, all years
    :return line graph
    """
    # latest year & month in dataset, as the dataset might not be complete (e.g till May 2025)
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # filter dataframe for last N years
    df.loc[:, "Year"] = df["DateTime"].dt.year
    if last_n_years is not None:
        all_years_sorted = sorted(df["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df = df[df["Year"].isin(selected_years)]

    # Histogram of delay duration
    fig = px.histogram(
        df, x="Min Delay", nbins=100,
        title="Distribution of TTC Delay Durations",
        labels={"Min Delay": "Delay Duration (minutes)", "count": "Number of Delays"}
    )

    max_delay = df["Min Delay"].max()
    print("YOLO")
    print(max_delay)
    fig.update_xaxes(range=[20, 60])  # force x-axis to the data max

    return fig

def plot_major_delay_trend(df, last_n_years: int = None) -> go.Figure:
    """Line graph showing delay trends over the years, of the stations that are consistently ranked in the
    top-N stations with delays
    df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: Ranked top-N stations
    :param last_n_years: last n years to analyze, if none, all years
    :return line graph
    """
    # latest year & month in dataset, as the dataset might not be complete (e.g till May 2025)
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # filter dataframe for last N years
    df.loc[:, "Year"] = df["DateTime"].dt.year
    if last_n_years is not None:
        all_years_sorted = sorted(df["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df = df[df["Year"].isin(selected_years)]

    df["Major Delay"] = df["Min Delay"] >= 20

    df["Year"] = df["DateTime"].dt.year

    major_counts = (
        df.groupby("Year")["Major Delay"]
        .sum()
        .reset_index(name="Major Delays")
    )

    fig = px.line(
        major_counts,
        x="Year", y="Major Delays",
        markers=True,
        title="TTC Delays Over Time: Trend of Major TTC Delays (>20 minutes)",
        labels={"Major Delays": "Number of Delays"}
    )

    # add annotation if dataset is not complete (e.g. till May 2025)
    if latest_month != "December":
        latest_value =\
            major_counts.loc[major_counts["Year"] == latest_year, "Major Delays"].item()
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift = 30,
            xshift=40,
            font=dict(color="black", size=12)
        )

    # Add covid annotation
    fig.add_annotation(
        x=2020,
        y=major_counts.loc[major_counts["Year"] == 2020, "Major Delays"].item(),
        text=f"COVID-19",
        showarrow=False,
        yshift=30,
        font=dict(color="black", size=12)
    )
    return fig

def plot_minor_delay_trend(df, last_n_years: int = None) -> go.Figure:
    """Line graph showing delay trends over the years, of the stations that are consistently ranked in the
    top-N stations with delays
    df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: Ranked top-N stations
    :param last_n_years: last n years to analyze, if none, all years
    :return line graph
    """
    # latest year & month in dataset, as the dataset might not be complete (e.g till May 2025)
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    # filter dataframe for last N years
    df.loc[:, "Year"] = df["DateTime"].dt.year
    if last_n_years is not None:
        all_years_sorted = sorted(df["Year"].unique())
        selected_years = all_years_sorted[-last_n_years:]
        df = df[df["Year"].isin(selected_years)]

    df["Minor Delay"] = df["Min Delay"] < 20

    df["Year"] = df["DateTime"].dt.year

    major_counts = (
        df.groupby("Year")["Minor Delay"]
        .sum()
        .reset_index(name="Minor Delay")
    )

    fig = px.line(
        major_counts,
        x="Year", y="Minor Delay",
        markers=True,
        title="TTC Delays Over Time: Trend of Minor TTC Delays (<20 minutes)",
        labels={"Minor Delay": "Number of Delays"}
    )

    # add annotation if dataset is not complete (e.g. till May 2025)
    if latest_month != "December":
        latest_value =\
            major_counts.loc[major_counts["Year"] == latest_year, "Minor Delay"].item()
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"till {latest_month} {latest_year}",
            showarrow=False,
            yshift = 30,
            xshift=40,
            font=dict(color="black", size=12)
        )

    # Add covid annotation
    fig.add_annotation(
        x=2020,
        y=major_counts.loc[major_counts["Year"] == 2020, "Minor Delay"].item(),
        text=f"COVID-19",
        showarrow=False,
        yshift=30,
        font=dict(color="black", size=12)
    )
    return fig
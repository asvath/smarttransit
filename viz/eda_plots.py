import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from viz.eda_utils import get_consistently_top_stations
from config import VALID_UNITS, CONVERSION_FACTORS

def annotate(df: pd.DataFrame, yearly: pd.DataFrame, fig: go.Figure) ->  go.Figure:
    """
    Adds annotation for Covid-19 and for the latest year if it's incomplete (e.g. Till Aug 2025)
    :param df: pd.DataFrame
    :param yearly: pd.DataFrame, grouped by year
    :param fig: go.Figure
    :return:
    """
    # latest year & month in dataset
    latest_date = df["DateTime"].max()
    latest_year = latest_date.year
    latest_month = latest_date.strftime("%B")  # e.g. "May"

    if latest_month != "December":
        latest_value = yearly[yearly["Year"] == latest_year]["Total Delay"].max()  # Total Delay in the latest year
        fig.add_annotation(
            x=latest_year,
            y=latest_value,
            text=f"Till {latest_month} {latest_year}",
            showarrow=False,
            yshift=10,  # move label a little above the bar
            font=dict(color="black", size=12)
        )

    # add covid-19 annotation if we have data for 2020
    subset = yearly.loc[yearly["Year"] == 2020]
    if not subset.empty:
        fig.add_annotation(
            x=2020,
            y=yearly.loc[yearly["Year"] == 2020]["Total Delay"].max(),
            text=f"COVID-19",
            showarrow=False,
            yshift=10,  # move label a little above the bar
            font=dict(color="black", size=12)
        )

    return fig



def plot_total_delay_by_year(df:pd.DataFrame, unit: str = "minutes", graphtype: str = "bar") -> go.Figure:
    """
    Plots the total delay in given units (min, hours, days) by year
    :param df: pd.Dataframe of TTC delays
    :param unit: measurement of the delay in minutes, hours or days
    :param graphtype: bar or line
    :return: plot
    """
    # Group by year and sum delays
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

    yearly = (
        df.groupby(df["DateTime"].dt.year.rename("Year"))["Min Delay"]
          .sum()
          .reset_index(name="Total Delay")
    )

    # apply conversion
    yearly["Total Delay"] = yearly["Total Delay"] / factors[unit]

    if graphtype == "bar":
        fig = px.bar(
            yearly,
            x="Year",
            y="Total Delay",
            title=f"TTC Delay: {unit.capitalize()} Lost per Year",
            labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
        )
    else:
        fig = px.line(
            yearly,
            x="Year",
            y="Total Delay",
            title=f"TTC Delay: {unit.capitalize()} Lost per Year",
            labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
        )

    fig = annotate(df,yearly,fig)

    return fig

def plot_delay_category_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
    """
    Plot top-N delay category trends per year
    :param df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n delay categories (e.g. Patrons, Mechanical/Infrastructure)
    :return: plot
    """
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

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
        title=f"TTC Delay: Top {top_n} Delay Categories by {unit.capitalize()} Lost per Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
    )

    fig = fig.for_each_xaxis(lambda ax: ax.update(categoryorder="total descending"))
    fig = annotate(df, yearly_cat, fig)

    return fig

def plot_delay_description_trend_by_year(df:pd.DataFrame, category:str = None, unit: str = "minutes", top_n: int = 5)\
        -> go.Figure:
    """
    Plot top-N delay descriptions for given category per year
    :param df: pd.DataFrame
    :param category: delay category, e.g. Patron,  Mechanical/Infrastructure
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n delay descriptions for category (e.g. for Patron: disorderly patron, in contact with train etc)
    :return: plot
    """
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

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

    if category:
        title=f"TTC Delay: Top {top_n} {category} Delays by {unit.capitalize()} Lost per Year"
    else:
        title = f"TTC Delay: Top {top_n} Delays by {unit.capitalize()} Lost by Year"


    fig = px.bar(
        top_n_cat,
        x="Year",
        y="Total Delay",
        color= "Delay Description",
        barmode="group",
        title=title,
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} Lost"}
    )

    fig = fig.for_each_xaxis(lambda ax: ax.update(categoryorder="total descending"))

    fig = annotate(df,yearly_cat,fig)

    return fig

def plot_station_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
    """
    Plot the top n stations with delays by year
    :param df: pd.DataFrame of TTC delay
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: top n categories of delay
    :return:
    """
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS
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
        title=f"TTC Delays: Top {top_n} stations by {unit.capitalize()} Lost per Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} lost"}
    )

    fig = annotate(df, yearly_cat, fig)
    return fig



def plot_consistently_top_station_trend(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5,
                                        last_n_years: int = None) -> go.Figure:
    """Bar graph showing delay trends over the years, of the stations that are consistently ranked in the
    top-N stations with delays
    :param df: pd.DataFrame
    :param unit: measurement of the delay in minutes, hours or days
    :param top_n: Ranked top-N stations
    :param last_n_years: last n years to analyze, if none, all years
    :return line graph
    """
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

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
        title=f"TTC Delays: Stations that are consistently in the Top {top_n} stations by {unit.capitalize()} "
              f"Lost per Year",
        labels={
            "Year": "Year",
            "Total Delay": f"Delay: {unit.capitalize()} lost",
            "Station": "Station"
        }
    )
    # annotate covid-19, latest year
    fig = annotate(df, yearly, fig)
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
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

    yearly = (
        df.groupby([df["DateTime"].dt.year.rename("Year"), "Line"])["Min Delay"]
          .sum()
          .reset_index(name="Total Delay")
    )


    # apply conversion
    yearly["Total Delay"] = yearly["Total Delay"] / factors[unit]

    # plot bar graph
    fig = px.bar(
        yearly,
        x="Year",
        y="Total Delay",
        color= "Line",
        barmode= "group",
        title=f"TTC Delays: {unit.capitalize()} Lost per Year Across Lines",
        labels={ "Year": "Year", "Total Delay": f"{unit.capitalize()} Lost"},
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
    yearly["Year_offset"] = yearly["Year"] + yearly["Line"].map(offsets)
    for line in ["BD", "YU", "SHP"]:
        line_data = yearly[yearly["Line"] == line]
        fig.add_scatter(
            x=line_data["Year_offset"],  # shifted per line
            y=line_data["Total Delay"],
            mode="lines+markers",
            name=f"{line} Trend",
            line=dict(dash="dot")
        )

    fig.update_yaxes(rangemode="tozero")

    # add annotation for covid-19 and latest year
    fig = annotate(df, yearly, fig)

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
    if unit not in VALID_UNITS:
        raise ValueError("unit must be 'minutes', 'hours', or 'days'")

    # conversation factor
    factors = CONVERSION_FACTORS

    df = df.copy()
    df = df[df["IsWeekday"] == True]

    df["Year"] = df["DateTime"].dt.year
    rush = (
        df.groupby(["Year", "Rush Hour"], as_index=False)
        .agg(
            Delays=("Min Delay", "count"),  # number of delay events
            TotalMinutes=("Min Delay", "sum")  # total delay time in minutes (sum of Min Delay)
        )
        .rename(columns={"DateTime": "Year"})
    )

    # apply conversion
    rush["Total Delay"] = rush["TotalMinutes"] / factors[unit]

    label_map = {
        "Morning": "Morning: 6am – 9am",
        "Evening": "Evening: 3pm – 7pm",
        "Off-peak: Afternoon": "Off-Peak: Weekday 9am - 3pm",
        "Off-peak: Night" : "Off-peak: Weekday 7pm - 2am",
    }
    rush["Rush Hour"] = rush["Rush Hour"].replace(label_map)

    fig = px.bar(
        rush,
        x="Year",
        y="Total Delay",
        color="Rush Hour",
        barmode="group",
        title=f"TTC Delays: Peak vs. Off-peak by {unit.capitalize()} Lost per Year",
        labels={ "Total Delay": f"{unit.capitalize()} Lost"},
        category_orders = {"Rush Hour": ["Morning: 6am – 9am", "Off-Peak: Weekday 9am - 3pm",
                                         "Evening: 3pm – 7pm", "Off-peak: Weekday 7pm - 2am"]}  # forces order
    )

    # add annotation for covid 19 and latest year if it is not complete (e.g. till May 2025)
    fig = annotate(df, rush, fig)

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
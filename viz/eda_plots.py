import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_total_delay_by_year(df:pd.DataFrame, unit: str = "minutes") -> go.Figure:
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

    fig = px.bar(
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

def plot_category_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
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

def plot_station_trend_by_year(df:pd.DataFrame, unit: str = "minutes", top_n: int = 5) -> go.Figure:
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

    top_n_cat =(
        yearly_cat.sort_values(["Year", "Total Delay"], ascending = [True, False]) # sort rows by year and total delay
        .groupby(yearly_cat["Year"]).head(top_n)
    )

    fig = px.line(
        top_n_cat,
        x="Year",
        y="Total Delay",
        color= "Station",
        title=f"TTC Delay by Category over Time measured in {unit.capitalize()} lost by Year",
        labels={ "Year": "Year", "Total Delay": f"Delay: {unit.capitalize()} lost"}
    )

    return fig
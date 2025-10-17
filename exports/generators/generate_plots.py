import os

from viz.eda_plots import (plot_total_delay_by_year, plot_delay_category_trend_by_year,
                           plot_delay_description_trend_by_year, plot_line_trends_by_year, plot_station_trend_by_year,
                           plot_rush_hour_trends_by_year,
                           plot_season_trends_by_year, plot_major_delay_trend, plot_minor_delay_trend,
                           plot_weekday_weekend_trends_by_year, plot_delay_category_trend_for_major_delay)
from viz.eda_utils import fig_to_html
from utils.ttc_loader import TTCLoader
from config import EXPORTS_PLOTS_DIR

# ensure folder exists
os.makedirs(EXPORTS_PLOTS_DIR, exist_ok=True)

loader = TTCLoader()
df = loader.df

# ### system-wide analysis
# total delay by year
fig = plot_total_delay_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "total_delay_by_year")

# # top delay category trends by year
fig = plot_delay_category_trend_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "delay_category_trend_by_year")

# top delay trends for patron category by year
df = loader.filter_category("Patron").df
fig = plot_delay_description_trend_by_year(df, "Patron", "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "patron_delay_trends_by_year")

# top delay trends for Mechanical/Infrastructure by year
loader.clear_filters()
df = loader.filter_category("Mechanical/Infrastructure").df
fig= plot_delay_description_trend_by_year(df, "Mechanical/Infrastructure", unit = "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "mechanical_infrastructure_delay_trends_by_year")

# ### spatial and temporal patterns analysis
# line delay trends by year
loader.clear_filters()
df = loader.df
fig = plot_line_trends_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "line_delay_trends_by_year" )

# station delay trends by year
fig = plot_station_trend_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "station_delay_trends_by_year")

# rush hour delay trends
fig = plot_rush_hour_trends_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "rush_hour_delay_trends_by_year")

# season delay trends
fig = plot_season_trends_by_year(df, "days")
fig_to_html(fig,EXPORTS_PLOTS_DIR, "season_delay_trends_by_year")

# major delay trends
fig = plot_major_delay_trend(df)
fig_to_html(fig,EXPORTS_PLOTS_DIR, "major_delay_trends_by_year")

# minor delay trends
fig = plot_minor_delay_trend(df)
fig_to_html(fig,EXPORTS_PLOTS_DIR, "minor_delay_trends_by_year")

### Top delay trend analysis

# disorderly patron station trend
df = loader.filter_delay_code("SUDP").df
fig = plot_station_trend_by_year(df=df, unit="hours",
                                 title=f"TTC Delays (Disorderly Patron): Top stations by Hours Lost per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "disorderly_patron_station_delay_trends_by_year")

# fire on track level trend
loader.clear_filters()
df = loader.filter_delay_code("MUPLB").df
fig = plot_station_trend_by_year(df=df, unit="hours", top_n=10,
                                 title=f"TTC Delays (Fire on track level): Top stations by Hours Lost per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "fire_on_track_level_station_delay_trends_by_year")

# weekday vs. weekend
loader.clear_filters()
df = loader.df
fig = plot_weekday_weekend_trends_by_year(df=df)
fig_to_html(fig, EXPORTS_PLOTS_DIR, "weekday_weekend_delay_trends_by_year")

# delay trends for major delay
fig = plot_delay_category_trend_for_major_delay(df = df, unit = "days",
                                                title = f"TTC Delay: Top Delay Categories by Days Lost"
                                                        f" per Year (>=20 min)")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "delay_category_trend_for_major_delays_by_year")
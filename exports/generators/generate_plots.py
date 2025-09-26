from viz.eda_plots import (plot_total_delay_by_year, plot_delay_category_trend_by_year,
                           plot_delay_description_trend_by_year, plot_line_trends_by_year, plot_station_trend_by_year,
                           plot_consistently_top_station_trend, plot_rush_hour_trends_by_year)
from viz.eda_utils import fig_to_html
from utils.ttc_loader import TTCLoader
from config import EXPORTS_PLOTS_DIR

loader = TTCLoader()
df = loader.df

# ### system-wide analysis
# # total delay by year
# fig = plot_total_delay_by_year(df, "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "total_delay_by_year")
#
# # top 5 delay category trends by year
# fig = plot_delay_category_trend_by_year(df, "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "delay_category_trend_by_year")
#
# # top 5 delay trends for patron category by year
# df = loader.filter_category("Patron").df
# fig = plot_delay_description_trend_by_year(df, "Patron", "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "patron_delay_trends_by_year")
#
# # top 5 delay trends for Mechanical/Infrastructure by year
# loader.clear_filters()
# df = loader.filter_category("Mechanical/Infrastructure").df
# fig= plot_delay_description_trend_by_year(df, "Mechanical/Infrastructure", unit = "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "mechanical_infrastructure_delay_trends_by_year")
#
# ### spatial and temporal patterns analysis
# # line delay trends by year
# loader.clear_filters()
# df = loader.df
# fig = plot_line_trends_by_year(df, "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "line_delay_trends_by_year" )
#
# # station delay trends by year
# fig = plot_station_trend_by_year(df, "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "station_delay_trends_by_year")
#
#
# # station delay trends by year
# fig = plot_station_trend_by_year(df, "days")
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "station_delay_trends_by_year")
#
# # delay trends for stations that are consistently in the top 10 stations by time lost per year, for the last 3 years
# fig = plot_consistently_top_station_trend(df =df, unit= "days", top_n = 10, last_n_years=3)
# fig_to_html(fig, EXPORTS_PLOTS_DIR, "consistently_top_10_station_delay_trends_by_year")

# rush hour delay trends
fig = plot_rush_hour_trends_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "rush_hour_delay_trends_by_year")
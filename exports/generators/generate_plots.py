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
title = "total_delay_by_year"
fig = plot_total_delay_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# # top delay category trends by year
title = "delay_category_trend_by_year"
fig = plot_delay_category_trend_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# top delay trends for patron category by year
title = "patron_delay_trends_by_year"
df = loader.filter_category("Patron").df
fig = plot_delay_description_trend_by_year(df, "Patron", "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# top delay trends for Mechanical/Infrastructure by year
title = "mechanical_infrastructure_delay_trends_by_year"
loader.clear_filters()
df = loader.filter_category("Mechanical/Infrastructure").df
fig= plot_delay_description_trend_by_year(df, "Mechanical/Infrastructure", unit = "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "mechanical_infrastructure_delay_trends_by_year")
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

### spatial and temporal patterns analysis

# line delay trends by year
title = "line_delay_trends_by_year"
loader.clear_filters()
df = loader.df
fig = plot_line_trends_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title )
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station delay trends by year
title = "station_delay_trends_by_year"
fig = plot_station_trend_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# rush hour delay trends
title = "rush_hour_delay_trends_by_year"
fig = plot_rush_hour_trends_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# season delay trends
title = "season_delay_trends_by_year"
fig = plot_season_trends_by_year(df, "days")
fig_to_html(fig,EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# major delay trends
title = "major_delay_trends_by_year"
fig = plot_major_delay_trend(df)
fig_to_html(fig,EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# minor delay trends
title = "minor_delay_trends_by_year"
fig = plot_minor_delay_trend(df)
fig_to_html(fig,EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

### Top delay trend analysis

# disorderly patron station trend
title = "disorderly_patron_station_delay_trends_by_year"
df = loader.filter_delay_code("SUDP").df
fig = plot_station_trend_by_year(df=df, unit="hours",
                                 title=f"TTC Delays (Disorderly Patron): Top stations by Hours Lost per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# fire on track level trend
title = "fire_on_track_level_station_delay_trends_by_year"
loader.clear_filters()
df = loader.filter_delay_code("MUPLB").df
fig = plot_station_trend_by_year(df=df, unit="hours", top_n=10,
                                 title=f"TTC Delays (Fire on track level): Top stations by Hours Lost per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# weekday vs. weekend
title = "weekday_weekend_delay_trends_by_year"
loader.clear_filters()
df = loader.df
fig = plot_weekday_weekend_trends_by_year(df=df)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# delay trends for major delay
title = "delay_category_trend_for_major_delays_by_year"
fig = plot_delay_category_trend_for_major_delay(df = df, unit = "days",
                                                title = f"TTC Delay: Top Delay Categories by Days Lost"
                                                        f" per Year (>=20 min)")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)
import os

from viz.eda_plots import (plot_total_delay_by_year, plot_delay_category_trend_by_year,
                           plot_delay_description_trend_by_year, plot_line_trends_by_year, plot_station_trend_by_year,
                           plot_rush_hour_trends_by_year,
                           plot_season_trends_by_year, plot_major_delay_trend, plot_minor_delay_trend,
                           plot_weekday_weekend_trends_by_year, plot_delay_category_trend_for_major_delay,
                           plot_total_delay_count_by_year, plot_avg_delay_time_by_year)
from viz.eda_utils import fig_to_html
from utils.ttc_loader import TTCLoader
from config import EXPORTS_PLOTS_DIR


# ensure folder exists
os.makedirs(EXPORTS_PLOTS_DIR, exist_ok=True)

# load data
loader = TTCLoader()
df = loader.df

### system-wide analysis
# total delay by year (time)
title = "total_delay_by_year"
fig = plot_total_delay_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# total delay by count
title = "total_delay_count_by_year"
fig = plot_total_delay_count_by_year(df)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# average time lost per delay
title = "avg_time_lost_per_delay_by_year"
fig = plot_avg_delay_time_by_year(df, "minutes", "line")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)



### top delay category trends by year
title = "delay_category_trend_by_year"
fig = plot_delay_category_trend_by_year(df, "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)


### patron analysis
# top delay trends for patron category by year
df = loader.filter_category("Patron").df
title = "patron_delay_trends_by_year"
fig = plot_delay_description_trend_by_year(df, "Patron", "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

##disorderly patron analysis
# number of disorderly patron delays per year
df = loader.filter_delay_code(["SUDP"]).df
title = "total_disorderly_patron_delay_count_by_year"
fig = plot_total_delay_count_by_year(df,"bar", f"TTC Delay: Number of Disorderly Patron Delays per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# avg delay mintues per disorderly patron incident
title = "avg_delay_minutes_per_disorderly_patron_by_year"
fig = plot_avg_delay_time_by_year(df, "minutes", "line",
                             "TTC Delay: Average Minutes Lost per Disorderly Patron Delay by Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station trends for disorderly patron
title = "station_delay_trends_by_year_disorderly_patron"
fig = plot_station_trend_by_year(df = df, top_n= 10,
                                 title= "TTC Delays: Top Stations by Number of Disorderly Patron Delays per Year",
                                 by_time= False)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

## track intrusion analysis
# clear filters
loader.clear_filters()
df = loader.filter_delay_code(["SUUT"]).df

# number of track intrusions per year
title = "total_track_intrusion_delay_count_by_year"
fig = plot_total_delay_count_by_year(df,"bar", f"TTC Delay: Number of Track Intrusion Delays per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# avg delay minutes per track intrusion incident
title = "avg_delay_minutes_per_track_intrusion_by_year"
fig = plot_avg_delay_time_by_year(df, "minutes", "line",
                             "TTC Delay: Average Minutes Lost per Track Intrusion Delay by Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station trends for track intrusion
title = "station_delay_trends_by_year_track_intrusion"
fig = plot_station_trend_by_year(df = df, top_n= 10,
                                 title= "TTC Delays: Top Stations by Number of Track Intrusion Delays per Year",
                                 by_time= False)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

## priority one analysis
# clear filters
loader.clear_filters()
df = loader.filter_delay_code(["MUPR1"]).df

# number of priority one per year
title = "total_priority_one_delay_count_by_year"
fig = plot_total_delay_count_by_year(df,"bar", f"TTC Delay: Number of Priority One Delays per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station trends for priority one
title = "station_delay_trends_by_year_priority_one"
fig = plot_station_trend_by_year(df = df, top_n= 5,
                                 title= "TTC Delays: Top Stations by Number of Priority One Delays per Year",
                                 by_time= False)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)


### top delay trends for Mechanical/Infrastructure by year
title = "mechanical_infrastructure_delay_trends_by_year"
loader.clear_filters()
df = loader.filter_category("Mechanical/Infrastructure").df
fig= plot_delay_description_trend_by_year(df, "Mechanical/Infrastructure", unit = "days")
fig_to_html(fig, EXPORTS_PLOTS_DIR, "mechanical_infrastructure_delay_trends_by_year")
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# track switch problem affecting routing
# number of track switch problems per year
df = loader.filter_delay_code(["PUSSW"]).df
title = "total_track_switch_delay_count_by_year"
fig = plot_total_delay_count_by_year(df,"bar", f"TTC Delay: Number of Track Switch Delays per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# avg delay minutes per track intrusion incident
title = "avg_delay_minutes_per_track_intrusion_by_year"
fig = plot_avg_delay_time_by_year(df, "minutes", "line",
                             "TTC Delay: Average Minutes Lost per Track Intrusion Delay by Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station trends for track switch
title = "station_delay_trends_by_year_track_switch"
fig = plot_station_trend_by_year(df = df, top_n= 10,
                                 title= "TTC Delays: Top Stations by Number of Track Switch Delays per Year",
                                 by_time= False)
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

### fire on track level analysis
loader.clear_filters()
df = loader.filter_delay_code(["MUPLB"]).df
title = "total_track_fire_delay_count_by_year"
fig = plot_total_delay_count_by_year(df,"bar", f"TTC Delay: Number of Track Fire Delays per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# avg delay minutes per track intrusion incident
title = "avg_delay_minutes_per_track_fire_by_year"
fig = plot_avg_delay_time_by_year(df, "minutes", "line",
                             "TTC Delay: Average Minutes Lost per Track Fire Delay by Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

# station trends for track fire
title = "fire_on_track_level_station_delay_trends_by_year"
fig = plot_station_trend_by_year(df=df, unit="hours", top_n=10,
                                 title=f"TTC Delays (Fire on track level): Top stations by Hours Lost per Year")
fig_to_html(fig, EXPORTS_PLOTS_DIR, title)
fig.write_image(f"{EXPORTS_PLOTS_DIR}/{title}.png", scale=2, width=1200, height=700)

### spatial and temporal patterns analysis
loader.clear_filters()
df = loader.df

# line delay trends by year
title = "line_delay_trends_by_year"
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

# weekday vs. weekend
title = "weekday_weekend_delay_trends_by_year"
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

import os

from config import LOG_DIR
def log_unique_stations_by_category(df, log_dir = LOG_DIR):
    """
    Logs unique station names by each category into separate text files.
    :param df: pd.DataFrame
    :param log_dir:
    :return:None
    """

    for category in ['passenger', 'non-passenger', 'unknown']:
        stations_in_category = df[df['Station Category'] == category]['Station'].unique()
        stations_in_category.sort()
        log_path = os.path.join(log_dir, 'stations_{category}.txt' )
        with open(log_path, 'w', encoding='utf-8') as f:
            for station in stations_in_category:
                f.write(station + '\n')
        print(f"Logged stations in {category} category to {log_path}")

def log_station_names_with_directionals(df, log_dir = LOG_DIR):
    """
    Logs station names with directionals into log file.
    :param df: pd.Dataframe
    :return: None
    """

    mask = df['Station'].str.contains(r'\b(to|toward|towards)\b', case=False, na=False)
    station_spans = df[mask]
    log_path = os.path.join(LOG_DIR, "station_spans_with_to_towardx.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        for station in station_spans['Station'].unique():
            f.write(station + "\n")
    print(f"Logged {len(station_spans)} station span entries to {log_path}")

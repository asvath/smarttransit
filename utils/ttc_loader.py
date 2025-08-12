import os

import pandas as pd

from config import PROCESSED_DATA_DIR
from utils import file_utils

class TTCLoader:
    """
    Lightweight loader for TTC delay data
    """

    def __init__(self, processed_data_dir = PROCESSED_DATA_DIR):
        self.processed_data_dir = processed_data_dir


    def _get_latest_file(self):
        # Step 1: Get all subfolders
        folders = [os.path.join(self.processed_data_dir, d) for d in os.listdir(self.processed_data_dir)
                   if os.path.isdir(os.path.join(self.processed_data_dir, d))]

        if not folders:
            return None

        # Find the latest folder by modification time
        latest_folder = max(folders, key=os.path.getmtime)

        files = [os.path.join(latest_folder, f) for f in os.listdir(latest_folder)
                   if os.path.isfile(os.path.join(latest_folder, f))]

        if not files:
            return None

        # Find latest file by modification time
        latest_file = max(files, key=os.path.getmtime)

        return latest_file

    def load_data(self):
        latest_file = self._get_latest_file()
        if latest_file is None:
            raise FileNotFoundError("No processed files found.")
        df = file_utils.read_csv(latest_file)
        df['DateTime'] = pd.to_datetime(df['DateTime'],format='%Y-%m-%d %H:%M:%S',  # matches YYYY-MM-DD HH:MM:SS
            errors='coerce'
        )
        return df

    # ---------- Static filters ----------

    @staticmethod
    def get_selected_year(df, year:int):
        return df[df['DateTime'].dt.year == year]

    @staticmethod
    def get_selected_years(df, year_start:int, year_end:int):
        return df[df['DateTime'].dt.year.between(year_start, year_end)]

    @staticmethod
    def get_selected_stations(df, stations):
       return df[df['Station'].isin(stations)]

    @staticmethod
    def get_morning_rush_hour(df):
        return df[df['Rush Hour'] == "Morning"]

    @staticmethod
    def get_evening_rush_hour(df):
        return df[df['Rush Hour'] == "Evening"]

    @staticmethod
    def get_off_peak(df):
        return df[df['Rush Hour'] == "Off-peak"]

    @staticmethod
    def get_weekdays(df):
        return df[df['DateTime'].dt.weekday < 5]

    @staticmethod
    def get_weekend(df):
        return df[df['DateTime'].dt.weekday >= 5]

    @staticmethod
    def get_delay_code(df, code):
        return df[df["Code"] == code]

    @staticmethod
    def get_line(df, line):
        return df[df["Line"] == line]

    @staticmethod
    def get_bound(df, bound):
        return df[df["Bound"] == bound]

    @staticmethod
    def get_season(df, season):
        return df[df["Season"] == season]

    @staticmethod
    def get_month(df, month):
        return df[df["Month"] == month]

    @staticmethod
    def get_vehicle(df, vehicle):
        return df[df["Vehicle"] == vehicle]

    @staticmethod
    def get_selected_delay(df, min_start:int, min_end:int):
        return df[df['Min Delay'].between(min_start, min_end)]

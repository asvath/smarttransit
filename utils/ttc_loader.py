import os
from typing import Self

import pandas as pd

from config import PROCESSED_DATA_DIR, CODE_DESC_DIR
from utils import file_utils
from utils.clean_utils import clean_delay_code_descriptions


class TTCLoader:
    """
    Lightweight loader for TTC delay data
    """

    def __init__(self, processed_data_dir = PROCESSED_DATA_DIR, autoload = True):
        self.processed_data_dir = processed_data_dir
        self.df_orig = None
        self.df = None
        self.delay_code_descriptions = None
        if autoload:
            self.delay_code_descriptions = self._load_code_descriptions()
            df = self._load_data()
            self.df_orig = df # cached df
            self.df = df.copy()

    @staticmethod
    def _load_code_descriptions():
        """Load Delay code and corresponding description"""
        code_descriptions_path = os.path.join(CODE_DESC_DIR, "Clean Code Descriptions.csv")
        df = file_utils.read_csv(code_descriptions_path)
        return dict(zip(df["CODE"], df["DESCRIPTION"]))

    def _get_latest_file(self) -> str | None:
        """Get filename of the most recently processed data"""
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

    def _load_data(self) -> pd.DataFrame:
        """Load most recently processed data"""
        latest_file = self._get_latest_file()
        if latest_file is None:
            raise FileNotFoundError("No processed data found.")
        df = file_utils.read_csv(latest_file)
        df['DateTime'] = pd.to_datetime(df['DateTime'],format='%Y-%m-%d %H:%M:%S',  # matches YYYY-MM-DD HH:MM:SS
            errors='coerce'
        )
        df['Min Delay'] = pd.to_numeric(df['Min Delay'], errors='coerce')
        df['Min Gap'] = pd.to_numeric(df['Min Gap'], errors='coerce')
        df['Vehicle'] = pd.to_numeric(df['Vehicle'], errors='coerce')

        # check if columns have nans
        bad_columns = df.isna().any()

        # check if entire dataframe has any nans:
        assert not bad_columns.any(), f"NaNs found in columns: {bad_columns[bad_columns].index.tolist()}"

        return df


    def reload(self) -> Self:
        """Reset working df from in-memory."""
        if self.df_orig is None:
            # If nothing cached yet, load from disk once.
            df = self._load_data()
            self.df_orig = df
            self.df = df.copy()
        else:
            self.df = self.df_orig.copy()
        return self

    # ---------- Filters ----------

    def get_selected_year(self, year:int) -> Self:
        """Filter data by year"""
        self.df = self.df[self.df['DateTime'].dt.year == year].copy()
        return self


    def get_selected_years(self, year_start:int, year_end:int) -> Self:
        """Filter data by year range"""
        self.df = self.df[self.df['DateTime'].dt.year.between(year_start, year_end)].copy()
        return self

    def get_month(self, month)-> Self:
        """Filter data by month"""
        self.df = self.df[self.df["Month"] == month].copy()
        return self

    def get_selected_delay(self, min_start:int, min_end:int)-> Self:
        """Filter data by delay time range"""
        self.df = self.df[self.df['Min Delay'].between(min_start, min_end)].copy()
        return self

    def get_morning_rush_hour(self)-> Self:
        """Filter data by morning rush hour"""
        self.df = self.df[self.df['Rush Hour'] == "Morning"].copy()
        return self

    def get_evening_rush_hour(self)-> Self:
        """Filter data by evening rush hour"""
        self.df = self.df[self.df['Rush Hour'] == "Evening"].copy()
        return self

    def get_off_peak(self)-> Self:
        """Filter data by off-peak time"""
        self.df = self.df[self.df['Rush Hour'] == "Off-peak"].copy()
        return self

    def get_weekdays(self)-> Self:
        """Filter data by weekdays"""
        self.df = self.df[self.df['DateTime'].dt.weekday < 5].copy()
        return self

    def get_weekend(self)-> Self:
        """Filter data by weekend"""
        self.df = self.df[self.df['DateTime'].dt.weekday >= 5].copy()
        return self

    def get_selected_stations(self, stations: list)-> Self:
        """Filter data by station name"""
        self.df = self.df[self.df['Station'].isin(stations)].copy()
        return self

    def get_delay_code(self, code)-> Self:
        """Filter data by delay code"""
        self.df = self.df[self.df["Code"] == code].copy()
        return self

    def get_line(self, line)-> Self:
        """Filter data by line"""
        self.df = self.df[self.df["Line"] == line].copy()
        return self

    def get_bound(self, bound)-> Self:
        """Filter data by bound"""
        self.df = self.df[self.df["Bound"] == bound].copy()
        return self

    def get_season(self, season)-> Self:
        """Filter data by season"""
        self.df = self.df[self.df["Season"] == season].copy()
        return self

    def get_vehicle(self, vehicle)-> Self:
        """Filter data by vehicle number"""
        self.df = self.df[self.df["Vehicle"] == vehicle].copy()
        return self

    def get_delay_code_description(self, code:str) -> Self:
        """Get delay code description"""
        return self.delay_code_descriptions[code]

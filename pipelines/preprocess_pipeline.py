from preprocess_delay_codes import clean_delay_codes
from preprocess_dataframe import clean_dataframe

"""
The TTC subway data pre-processing pipeline.

Steps:
- Cleans TTC delay code descriptions (removes non-ASCII chars, saves cleaned file)
- Merges and cleans raw TTC subway delay data (standardizes fields, removes invalid records, adds helper columns)
- Logs key processing steps for manual verification

Run this script to generate a cleaned TTC subway delay dataset.
"""

def preprocess_pipeline():
    clean_delay_codes()
    clean_dataframe()


if __name__ =="__main__":
    preprocess_pipeline()


from utils import clean_utils
"""
Cleans TTC delay code descriptions, removes all non-ASCII characters
from the text fields, and saves a cleaned version to disk.
"""
def clean_delay_codes():
    clean_utils.clean_delay_code_descriptions()

if __name__ == "__main__":
    clean_delay_codes()
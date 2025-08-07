This project explores Toronto's TTC subway delay data to understand operational inefficiencies, safety risks, and equity concerns across the system. Our key research questions are organized into four categories:

I. System-Wide Trends

    Has the number of minutes in delay increased over the years?

    Which types of delays cause the most total disruption?

    What are the most common causes of delays — and have they changed over time?

II. Root Cause & Infrastructure Analysis

    Signal issues — Are particular vehicles or train models consistently affected?

    Security incidents (by station) — Are some stations seeing a rise over the years? (→ Supports platform door recommendations)

    Security incidents (by time) — Are there time patterns (e.g., late-night spikes)?

III. Spatial & Temporal Patterns

    Which stations experience the most frequent or severe delays?

    Which subway lines are most delay-prone?

    When do delays occur most often — during peak or off-peak hours?

    Which months have the most delays (e.g., winter-related issues)?

    Are delays clustered around major city events?

IV. Equity & Impact

    Do delays disproportionately affect neighborhoods with fewer transit alternatives?
## Installation

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```
```
## Project Structure
SmartTransit/
│
├── data/
│   ├── raw/
│   │   ├── code_descriptions/
│   │   │   ├── ttc-subway-delay-codes.xlsx
│   │   │   └── Code Descriptions.csv
│   │   ├── delays/
│   │   │   ├── ttc-subway-delay-data-2018.xlsx
│   │   │   ├── ttc-subway-delay-data-2019.xlsx
│   │   │   └── ... (all other raw data files)
│   │   ├── docs/
│   │   │   ├── ttc-subway-delay-data-readme.xlsx
│   │   │   └── ttc_subway_stations_with_linecodes.txt
│   │   └── dropped_raw/
│   │        └── ... (csvs containing data dropped during cleaning)
│   ├── interim/        # Partially cleaned/intermediate data
│   └── processed/      # Final cleaned dataset
│
├── logs/               # Logs of cleaning steps and errors
├── pipelines/          # Pipeline scripts
├── utils/              # Utility modules
├── config.py           # Configuration file
└── README.md
```
Key Folders & Files

    data/raw/code_descriptions/
    Delay code files and descriptions.

    data/raw/delays/
    Raw TTC subway delay Excel files (2018–2025).

    data/raw/docs/
    Official TTC documentation and station reference file (ttc_subway_stations_with_linecodes.txt).

    data/raw/dropped_raw/
    CSVs of raw data dropped during cleaning for transparency/debugging.

    data/interim/
    Partially cleaned or in-progress data.

    data/processed/
    Final cleaned datasets, ready for analysis.

    logs/
    Logs of cleaning steps and errors.

    pipelines/
    Main data cleaning and processing scripts.

    utils/
    Utility Python modules (for loading, cleaning, etc).

    config.py
    Project and pipeline configuration file
The reference file ttc_subway_stations_with_linecodes.txt (located in data/raw/docs/) lists all 
valid operational subway stations along with their line codes. 
This is used in the preprocessing pipeline to standardize and validate station names, 
and to categorize stations as passenger, non-passenger, or unknown.

## Preprocessing of Raw TTC dataset
Data Cleaning & Preprocessing

### 📂 Raw Data Overview

The raw TTC dataset consists of:

    Excel files containing subway delay event data (2018 – June 2025)

    Delay code files mapping codes to event descriptions

    Delay data README file with column names and descriptions

### Cleaning Pipeline Steps

A reference text file listing all valid operational station names with subway line codes (e.g. ROSEDALE STATION [YU]) was created for cleaning and validation:
data/raw/docs/ttc_subway_stations_with_linecodes.txt
1. Clean Delay Codes & Descriptions

    Remove non-ASCII characters from delay code files

    Output a cleaned mapping for consistent use downstream

2. Merge & Clean Raw Delay Data

    Merge all raw TTC delay files into one dataframe
    (Log file names used for the merge and any errors)

    Drop rows where:

        Any key column (Min delay, Min Gap, Vehicle) is missing or zero

        Min Gap < Min delay (since the gap between trains should exceed the delay)

    Write out dropped data to: data/raw/dropped_raw/

3. Standardize Station Names

    Remove embedded line codes (e.g. "YU", "BD") from station names

    Standardize abbreviations (e.g. "St" to "St.")

    Correct spelling errors

    Ensure all passenger station names end with "STATION"
    (unless the name ends with YARD, HOSTLER, WYE, POCKET, TAIL, or TRACK, which are legitimate endings for non-passenger stations)

    Standardize naming for dual-line interchange stations (e.g. "BLOOR-YONGE", "SHEPPARD-YONGE")

4. Station Categorization

    Tag stations as:

        passenger (if listed in the valid operational stations file)

        non-passenger (if ending with yard/hostler/etc)

        unknown (stations that can't be matched, e.g. SRT, severe typos, or with directional suffixes)

    Drop all unknown stations from analysis and write them out to data/raw/dropped_raw/

5. Validate Delay Codes

    Ensure all event codes match the cleaned delay code mapping

    Errors are set to NaN as we do not know which is the correct delay code

6. Validate Bound (Direction)

    For valid passenger stations, check if the direction (Bound) matches the station’s subway line
    (e.g. ROSEDALE STATION, YU, E is set to NaN as YU is only N or S)

    Set to NaN if not valid

7. Clean & Standardize Date/Time

    Standardize all date and time columns as strings

    Combine into a new DateTime column as pandas datetime objects (enables hour, weekday, and time-based analysis)

8. Correct Day of Week

    Recompute Day using the DateTime to ensure accuracy

9. Add Useful Features

    IsWeekday: True/False

    Rush Hour: Categorical ("Morning", "Evening", "Off Peak", "Weekend")

    Season: Categorical (e.g. "Winter", "Spring", etc)

10. Logging & Output

    Log all cleaned stations by category for manual review

    Write out the final cleaned dataset to: data/processed/

#### How to Run

Make sure your working directory is set to the project root (SmartTransit/).

To run the data cleaning & preprocessing pipeline, use the following command in your terminal:

    python pipelines/preprocess_pipeline.py

If you are running from a different location, provide the full path

## Delay Code Classification Logic

We manually categorized TTC subway delay codes using the following logic:

- **Mechanical:** Failures of transit infrastructure or equipment (track, signals, motors, brakes, etc.)
- **Human/Process:** Staff/operator mistakes or maintenance errors
- **Weather:** Delays due to natural events (snow, ice, flood, heat, etc.)
- **Patron:** Incidents caused by customers or the public (medical, disorderly, trespassing, vandalism, etc.)
- **Other/External:** Labor disputes, security, systemwide outages, power failures (external), or any ambiguous causes


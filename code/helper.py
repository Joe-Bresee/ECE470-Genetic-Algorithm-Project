import pandas as pd
import os

# Load the file again just to search for the correct ID
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CENSUS_CSV_PATH = os.path.join(SCRIPT_DIR, "98-401-X2021006_English_CSV_data_BritishColumbia.csv")
df = pd.read_csv(CENSUS_CSV_PATH, nrows=50000, encoding="latin-1")

# Look at rows around the transit ID to find walk/bike
# We look for IDs 2607 to 2612
relevant_ids = df[df["CHARACTERISTIC_ID"].isin([2607, 2608, 2609, 2610, 2611])]
print(relevant_ids[["CHARACTERISTIC_ID", "CHARACTERISTIC_NAME"]].drop_duplicates())
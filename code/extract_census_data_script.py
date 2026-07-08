# TODO: find where commute data actually is, its currently zero.
# TODO: accidentally deleted some sort of something in data/.

import folium
import geopandas as gpd
import pandas as pd
import requests, zipfile, io, os

# Your shapefile setup
SHAPEFILE_URL = "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/files-fichiers/lda_000b21a_e.zip"
SHAPEFILE_DIR = "da_boundaries"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CENSUS_CSV_PATH = os.path.join(SCRIPT_DIR, "98-401-X2021006_English_CSV_data_BritishColumbia.csv")

VICTORIA_BBOX = {
    "min_lat": 48.35, "max_lat": 48.55,
    "min_lon": -123.6, "max_lon": -123.2
}

def download_and_extract(url, extract_to):
    print(f"Downloading {url} ...")
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(extract_to)
    print(f"Extracted to {extract_to}/")

if not os.path.exists(SHAPEFILE_DIR):
    download_and_extract(SHAPEFILE_URL, SHAPEFILE_DIR)

# --- 1. Load shapefile and clip to Victoria ---
print("Clipping shapefiles to Victoria...")
shp_path = os.path.join(SHAPEFILE_DIR, "lda_000b21a_e.shp")
gdf = gpd.read_file(shp_path)
gdf = gdf.to_crs(epsg=4326)
gdf = gdf.cx[
    VICTORIA_BBOX["min_lon"]:VICTORIA_BBOX["max_lon"],
    VICTORIA_BBOX["min_lat"]:VICTORIA_BBOX["max_lat"]
]

# Extract the list of valid DGUIDs that actually fall in Victoria
victoria_dguids = set(gdf["DGUID"].tolist())
print(f"Found {len(victoria_dguids)} Dissemination Areas in Victoria BBox.")

# --- 2. Load and filter the Census CSV ---
print("Extracting census data for Victoria DAs...")
TARGET_VARIABLES = {
    1:    "population",
    340:  "low_income_count",
    2603: "commute_total",
    2607: "commute_transit",
    2608: "commute_walk",
    2609: "commute_bike"
}

cols_to_use = ["DGUID", "GEO_LEVEL", "CHARACTERISTIC_ID", "C1_COUNT_TOTAL"]
chunks = []

# Warning this things massive chunk it and its in latin-1 for some reaosn
for chunk in pd.read_csv(CENSUS_CSV_PATH, usecols=cols_to_use, chunksize=50000, low_memory=False, encoding="latin-1"):
    # Filter by Victoria DGUIDs AND our specific target variables
    da_chunk = chunk[
        (chunk["DGUID"].isin(victoria_dguids)) & 
        (chunk["CHARACTERISTIC_ID"].isin(TARGET_VARIABLES.keys()))
    ]
    chunks.append(da_chunk)
    
df = pd.concat(chunks, ignore_index=True)

# Pivot and process equity data
print("Processing equity and population metrics...")
df_pivot = df.pivot(index="DGUID", columns="CHARACTERISTIC_ID", values="C1_COUNT_TOTAL").reset_index()

# Safely rename columns ONLY if they exist in the pivot table
rename_dict = {k: v for k, v in TARGET_VARIABLES.items() if k in df_pivot.columns}
df_pivot = df_pivot.rename(columns=rename_dict)

# Failsafe: Ensure all required columns exist so math operations don't crash
for col in TARGET_VARIABLES.values():
    if col not in df_pivot.columns:
        print(f"⚠️ Warning: Could not find data for '{col}'. Defaulting to 0.")
        df_pivot[col] = 0  # Create the missing column with zeros
        
    # Convert to numeric safely
    df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce').fillna(0)

# Calculate percentages safely (Division by zero is already handled)
df_pivot["pct_low_income"] = df_pivot.apply(lambda row: row["low_income_count"] / row["population"] if row["population"] > 0 else 0, axis=1)
df_pivot["pct_transit_reliant"] = df_pivot.apply(lambda row: (row["commute_transit"] + row["commute_walk"] + row["commute_bike"]) / row["commute_total"] if row["commute_total"] > 0 else 0, axis=1)

# Normalize to 0-1 range
max_income = df_pivot["pct_low_income"].max() or 1
max_transit = df_pivot["pct_transit_reliant"].max() or 1
df_pivot["pct_low_income_norm"] = df_pivot["pct_low_income"] / max_income
df_pivot["pct_transit_commute_mode_norm"] = df_pivot["pct_transit_reliant"] / max_transit

# Keep only what we need for mapping/GA
equity_df = df_pivot[["DGUID", "population", "pct_low_income_norm", "pct_transit_commute_mode_norm"]]

# --- 3. Merge Back to GeoDataFrame ---
gdf = gdf.merge(equity_df, on="DGUID", how="left")

# Clean up empty geometry or missing pop data
gdf = gdf[gdf["geometry"].is_valid & gdf["geometry"].notna()]
gdf["population"] = gdf["population"].fillna(0)

print(f"Final Data Prep Complete: {len(gdf)} DAs ready for mapping and Genetic Algorithm.")

# --- 6. Save the final data ---
# Save to GeoJSON so you can inspect it in QGIS or online tools
gdf.to_file("victoria_equity_data.geojson", driver="GeoJSON")
print("Saved victoria_equity_data.geojson")
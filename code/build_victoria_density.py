import os
import requests
import zipfile
import io
import pandas as pd
import geopandas as gpd

# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DATA_DIR = os.path.normpath(DATA_DIR)

os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(DATA_DIR, "victoria_density.geojson")

# -----------------------------
# URLs (Statistics Canada)
# -----------------------------
SHAPEFILE_URL = "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/files-fichiers/lda_000b21a_e.zip"
POPULATION_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/98100015-eng.zip"

# -----------------------------
# Victoria bounding box
# -----------------------------
VICTORIA_BBOX = {
    "min_lat": 48.35,
    "max_lat": 48.55,
    "min_lon": -123.6,
    "max_lon": -123.2
}


def download_and_extract(url, folder):
    os.makedirs(folder, exist_ok=True)

    print(f"Downloading: {url}")
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(folder)

    print(f"Extracted to: {folder}")


def load_population_table():
    print("Downloading population data...")
    r = requests.get(POPULATION_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))

    csv_name = [f for f in z.namelist() if f.endswith(".csv") and "Meta" not in f][0]

    df = pd.read_csv(z.open(csv_name), encoding="latin-1")

    df = df[df["DGUID"].str.startswith("2021S0512")]

    density_col = [c for c in df.columns if "density" in c.lower()][0]

    df = df[["DGUID", density_col]].copy()
    df.columns = ["DGUID", "pop_density"]
    df["pop_density"] = pd.to_numeric(df["pop_density"], errors="coerce")

    return df


def build_victoria_dataset():
    shp_dir = os.path.join(BASE_DIR, "..", "da_boundaries")
    shp_dir = os.path.normpath(shp_dir)

    if not os.path.exists(shp_dir):
        download_and_extract(SHAPEFILE_URL, shp_dir)

    shp_path = os.path.join(shp_dir, "lda_000b21a_e.shp")
    gdf = gpd.read_file(shp_path)

    gdf = gdf.to_crs(epsg=4326)

    gdf = gdf.cx[
        VICTORIA_BBOX["min_lon"]:VICTORIA_BBOX["max_lon"],
        VICTORIA_BBOX["min_lat"]:VICTORIA_BBOX["max_lat"]
    ]

    print(f"Victoria DAs after clip: {len(gdf)}")

    pop = load_population_table()

    gdf = gdf.merge(pop, on="DGUID", how="left")

    print(f"DAs with density: {gdf['pop_density'].notna().sum()}")

    # -----------------------------
    # SAVE INTO /data FOLDER
    # -----------------------------
    gdf.to_file(OUTPUT_FILE, driver="GeoJSON")

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_victoria_dataset()
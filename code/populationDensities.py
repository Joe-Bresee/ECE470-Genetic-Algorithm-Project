import folium
import geopandas as gpd
import pandas as pd
import requests, zipfile, io, os

SHAPEFILE_URL = "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/files-fichiers/lda_000b21a_e.zip"
POPULATION_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/98100015-eng.zip"

SHAPEFILE_DIR = "da_boundaries"
POPULATION_CSV = "98100015.csv"

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

if not os.path.exists(POPULATION_CSV):
    print(f"Downloading {POPULATION_URL} ...")
    r = requests.get(POPULATION_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    data_file = [f for f in z.namelist() if f.endswith(".csv") and "Meta" not in f][0]
    with open(POPULATION_CSV, "wb") as f:
        f.write(z.read(data_file))
    print(f"Saved {POPULATION_CSV}")

# --- Load shapefile and clip to Victoria first ---
shp_path = os.path.join(SHAPEFILE_DIR, "lda_000b21a_e.shp")
gdf = gpd.read_file(shp_path)
gdf = gdf.to_crs(epsg=4326)
gdf = gdf.cx[
    VICTORIA_BBOX["min_lon"]:VICTORIA_BBOX["max_lon"],
    VICTORIA_BBOX["min_lat"]:VICTORIA_BBOX["max_lat"]
]

# --- Load CSV, keep only DA-level rows, join on DGUID ---
pop = pd.read_csv(POPULATION_CSV, encoding="latin-1")
pop = pop[pop["DGUID"].str.startswith("2021S0512")]

density_col = [c for c in pop.columns if "density" in c.lower()][0]
pop = pop[["DGUID", density_col]].copy()
pop.columns = ["DGUID", "pop_density"]
pop["pop_density"] = pd.to_numeric(pop["pop_density"], errors="coerce")

gdf = gdf.merge(pop, on="DGUID", how="left")

print(f"Loaded {len(gdf)} DAs, {gdf['pop_density'].notna().sum()} with density data")

# --- Build map ---
center_lat = (VICTORIA_BBOX["min_lat"] + VICTORIA_BBOX["max_lat"]) / 2
center_lon = (VICTORIA_BBOX["min_lon"] + VICTORIA_BBOX["max_lon"]) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

folium.Choropleth(
    geo_data=gdf.to_json(),
    data=gdf,
    columns=["DGUID", "pop_density"],
    key_on="feature.properties.DGUID",
    fill_color="YlOrRd",
    fill_opacity=0.6,
    line_opacity=0.2,
    legend_name="Population density (per km²)",
    nan_fill_color="transparent",
    name="Population Density",
).add_to(m)

folium.GeoJson(
    gdf,
    style_function=lambda f: {"fillOpacity": 0, "weight": 0},
    tooltip=folium.GeoJsonTooltip(
        fields=["DAUID", "pop_density"],
        aliases=["DA ID", "Density (per km²)"],
        localize=True
    ),
).add_to(m)

folium.LayerControl().add_to(m)
m.save("density.html")
print("Saved density.html")
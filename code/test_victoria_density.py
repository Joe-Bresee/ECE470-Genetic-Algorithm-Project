import os
import geopandas as gpd
from shapely.geometry import Point

# -------------------------------------------------
# Load saved dataset using project-relative path
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "victoria_density.geojson")
DATA_PATH = os.path.normpath(DATA_PATH)

gdf = gpd.read_file(DATA_PATH)

print(f"Loaded {len(gdf)} dissemination areas")

# -------------------------------------------------
# Simple lookup function
# -------------------------------------------------
def get_density(lat, lon):
    point = Point(lon, lat)

    match = gdf[gdf.contains(point)]

    if match.empty:
        return None

    return float(match.iloc[0]["pop_density"])


# -------------------------------------------------
# Test coordinates (Victoria)
# -------------------------------------------------
test_points = [
    ("Downtown - Inner Harbour", 48.4219, -123.3707),
    ("Downtown - Yates & Blanshard", 48.4270, -123.3650),
    ("Fernwood Village", 48.4289, -123.3485),
    ("Cook Street Village", 48.4258, -123.3420),
    ("James Bay - Legislature", 48.4205, -123.3689),
    ("James Bay - Dallas Road", 48.4146, -123.3702),

    ("UVic Main Campus", 48.4634, -123.3111),
    ("Cadboro Bay Village", 48.4546, -123.3025),
    ("Saanich - Hillside Area", 48.4490, -123.3375),

    ("Esquimalt - Naval Base", 48.4336, -123.4116),
    ("Esquimalt - Highrock Park", 48.4395, -123.4082),

    ("Langford - City Centre", 48.4487, -123.5093),
    ("Langford - Goldstream Ave", 48.4515, -123.5042),

    ("View Royal - Admirals Rd", 48.4582, -123.4338),
    ("Colwood - West Shore Town Centre", 48.4396, -123.5008),

    ("Oak Bay - Oak Bay Ave", 48.4247, -123.3246),
    ("Oak Bay - Beach Drive", 48.4199, -123.3178),
]

for name, lat, lon in test_points:
    density = get_density(lat, lon)
    print(f"{name}: {density}")
import os
import json
import osmnx as ox
from collections import Counter
import math

def first_valid(*values):
    for v in values:
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            return v
    return None

CACHE_PATH = "pois.json"

POI_TAGS = {
    "amenity": [
        "school", "hospital", "clinic", "college", "university", "library",
        "pharmacy", "community_centre", "social_facility",
        "veterinary", "place_of_worship", "shelter", "food_bank",
        "restaurant",
    ],
    "shop": [
        "supermarket", "mall", "convenience",
        "hairdresser", "laundry",
    ],
    "healthcare": [
        "optometrist", "physiotherapist", "dialysis", "alternative",
    ],
    "leisure": ["sports_centre", "stadium"],
}

VICTORIA_BBOX = {
    "min_lat": 48.35, "max_lat": 48.55,
    "min_lon": -123.6, "max_lon": -123.2
}


def fetch_pois(bbox=VICTORIA_BBOX):
    print("Fetching POIs for Greater Victoria bbox from OSM...")
    ox_bbox = (bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])  # (west, south, east, north)

    pois = ox.features_from_bbox(ox_bbox, tags=POI_TAGS)

    records = []
    for _, row in pois.iterrows():
        geom = row.geometry
        if geom.geom_type == "Point":
            lat, lon = geom.y, geom.x
        else:
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x

        poi_type = first_valid(row.get("amenity"), row.get("shop"), row.get("leisure"), row.get("healthcare"))
        name = row.get("name", None)
        records.append({"lat": lat, "lon": lon, "type": poi_type, "name": name})

    print(f"Fetched {len(records)} POIs")
    return records


def load_or_fetch_pois(cache_path=CACHE_PATH):
    if os.path.exists(cache_path):
        print(f"Loading cached POIs from {cache_path}")
        with open(cache_path) as f:
            return json.load(f)

    pois = fetch_pois()
    with open(cache_path, "w") as f:
        json.dump(pois, f, indent=2)
    print(f"Saved {len(pois)} POIs to {cache_path}")
    return pois


if __name__ == "__main__":
    # quick isolated test first — confirm UVic shows up before running the full fetch
    ox_bbox = (VICTORIA_BBOX["min_lon"], VICTORIA_BBOX["min_lat"], VICTORIA_BBOX["max_lon"], VICTORIA_BBOX["max_lat"])
    test = ox.features_from_bbox(ox_bbox, tags={"amenity": "university"})
    print(f"University test: {len(test)} found")
    print(test.get("name"))

    pois = load_or_fetch_pois()

    type_counts = Counter(p["type"] for p in pois)
    for poi_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {poi_type}: {count}")
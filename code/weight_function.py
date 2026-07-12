# GENERAL TODO:
# choose snake case or camle case
# organize repo: /data for all data, /scripts for helper scripts, /code for code with further organization within it -> /genetic-algorithm, /data-processing, /UI...

import pandas as pd
import geopandas as gpd
import random
import math
import json
import os
import osmnx as ox
from shapely.geometry import LineString, Point

from busRoutes import randomStopsOnRoute, getRouteShape
from config import GA_CONFIG, ROUTE_NUMBER, WEIGHTS

shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")
stop_times = pd.read_csv("stop_times.txt")
stops = pd.read_csv("stops.txt")


def get_stops_for_routes(route_numbers, routes_df, trips_df, stop_times_df, stops_df):
    """Given a list of route_short_names (e.g. [14, 26]), return their stop coordinates."""
    route_numbers_str = [str(r) for r in route_numbers]
    route_ids = routes_df[routes_df["route_short_name"].astype(str).isin(route_numbers_str)]["route_id"]
    trip_ids = trips_df[trips_df["route_id"].isin(route_ids)]["trip_id"]
    stop_ids = stop_times_df[stop_times_df["trip_id"].isin(trip_ids)]["stop_id"].unique()
    matched_stops = stops_df[stops_df["stop_id"].isin(stop_ids)]
    return list(zip(matched_stops["stop_lat"], matched_stops["stop_lon"]))


# Precompute once, not per-generation — used by transfer/connectivity bonus
OTHER_ROUTE_NUMBERS_HARDCODED = [95, 14, 26]
_other_route_numbers = [r for r in OTHER_ROUTE_NUMBERS_HARDCODED if r != ROUTE_NUMBER]
OTHER_ROUTE_STOPS = get_stops_for_routes(_other_route_numbers, routes, trips, stop_times, stops)

# TODO (later): swap to all other routes instead of the hardcoded three
# _all_route_numbers = routes["route_short_name"].unique().tolist()
# _other_route_numbers = [r for r in _all_route_numbers if str(r) != str(ROUTE_NUMBER)]
# OTHER_ROUTE_STOPS = get_stops_for_routes(_other_route_numbers, routes, trips, stop_times, stops)


def haversine_m(p1, p2):
    """Distance in meters between two (lat, lon) points."""
    R = 6371000
    lat1, lon1 = map(math.radians, p1)
    lat2, lon2 = map(math.radians, p2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def enforce_min_spacing(stops, min_spacing):
    """
    Hard anti-clustering constraint, enforced at generation time (repair strategy).
    Drops any stop that's too close to an already-accepted stop, so invalid
    individuals are never created in the first place.
    """
    accepted = []
    for s in stops:
        if all(haversine_m(s, a) >= min_spacing for a in accepted):
            accepted.append(s)
    return accepted


def randomlyGenerateBusStops(routeNumber: int):
    routeShapes = getRouteShape(routeNumber, routes, trips, shapes)
    stops = []
    target_count = random.randint(GA_CONFIG["min_stops"], GA_CONFIG["max_stops"])

    for rNum, coords, color in routeShapes:
        candidate_stops = randomStopsOnRoute(coords, target_count)
        candidate_stops = enforce_min_spacing(candidate_stops, GA_CONFIG["min_spacing_meters"])
        stops = candidate_stops
        routeNumber = rNum

    return {"routeNumber": routeNumber, "stops": stops}


# --- Route-position helpers, used by spacing_penalty ---
_routeShapes = getRouteShape(ROUTE_NUMBER, routes, trips, shapes)
ROUTE_COORDS = _routeShapes[0][1]  # coords for the single route we're optimizing


def segmentLength(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def buildCumulativeDist(routeCoords):
    cumulativeDist = [0]
    for i in range(len(routeCoords) - 1):
        cumulativeDist.append(cumulativeDist[-1] + segmentLength(routeCoords[i], routeCoords[i + 1]))
    return cumulativeDist


CUMULATIVE_DIST = buildCumulativeDist(ROUTE_COORDS)


def positionAlongRoute(point, routeCoords=ROUTE_COORDS, cumulativeDist=CUMULATIVE_DIST):
    """
    Projects a point onto the route polyline, returns distance-along-route.
    Used so spacing_penalty doesn't need stops pre-sorted in route order —
    crossover/mutation in ga.py don't guarantee that ordering is preserved.
    """
    best_dist_along = 0
    best_perp_dist = float("inf")
    for i in range(len(routeCoords) - 1):
        p1, p2 = routeCoords[i], routeCoords[i + 1]
        segVec = (p2[0] - p1[0], p2[1] - p1[1])
        segLenSq = segVec[0] ** 2 + segVec[1] ** 2
        if segLenSq == 0:
            continue
        toPoint = (point[0] - p1[0], point[1] - p1[1])
        t = (toPoint[0] * segVec[0] + toPoint[1] * segVec[1]) / segLenSq
        t = max(0, min(1, t))
        proj = (p1[0] + t * segVec[0], p1[1] + t * segVec[1])
        perp_dist = segmentLength(point, proj)
        if perp_dist < best_perp_dist:
            best_perp_dist = perp_dist
            best_dist_along = cumulativeDist[i] + t * segmentLength(p1, p2)
    return best_dist_along


def spacing_penalty(stops):
    """
    Soft penalty rewarding even spacing along the route (hard minimum spacing
    is already enforced at generation time via enforce_min_spacing).
    """
    if len(stops) < 2:
        return 0
    positions = sorted(positionAlongRoute(s) for s in stops)
    gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
    totalLength = CUMULATIVE_DIST[-1]
    idealGap = totalLength / (len(stops) - 1)
    deviation = sum((g - idealGap) ** 2 for g in gaps)
    return deviation


# --- Equity-weighted coverage ---
EQUITY_GEOJSON_PATH = "victoria_equity_data.geojson"
DA_CRS_METRIC = "EPSG:32610"
COVERAGE_RADIUS_M = 400
ROUTE_BUFFER_M = 1000

_equity_gdf = gpd.read_file(EQUITY_GEOJSON_PATH)
_equity_gdf_metric = _equity_gdf.to_crs(DA_CRS_METRIC)
_centroids_wgs84 = _equity_gdf_metric.geometry.centroid.to_crs(_equity_gdf.crs)

# Single unified lookup — pop, equity vars, AND centroid all in one place per DGUID
EQUITY_LOOKUP = {}
for i, row in _equity_gdf.iterrows():
    EQUITY_LOOKUP[row["DGUID"]] = {
        "population": row["population"],
        "income": row["pct_low_income_norm"],
        "transit": row["pct_transit_commute_mode_norm"],
        "centroid": (_centroids_wgs84.iloc[i].y, _centroids_wgs84.iloc[i].x),  # (lat, lon)
    }


def get_das_near_route(route_coords, buffer_m=ROUTE_BUFFER_M):
    """
    Pre-filter step: which DAs are even worth checking for this route.
    Uses sindex so this is fast even against the full DA set — runs ONCE
    at module load, not per individual/generation.
    """
    route_line = LineString([(lon, lat) for lat, lon in route_coords])
    route_gdf = gpd.GeoDataFrame(geometry=[route_line], crs="EPSG:4326").to_crs(DA_CRS_METRIC)
    buffered_route = route_gdf.geometry.iloc[0].buffer(buffer_m)
    nearby_idx = _equity_gdf_metric.sindex.query(buffered_route, predicate="intersects")
    return _equity_gdf.iloc[nearby_idx]["DGUID"].tolist()


DAS_NEAR_ROUTE = get_das_near_route(ROUTE_COORDS)
print(f"Filtered to {len(DAS_NEAR_ROUTE)} DAs near route {ROUTE_NUMBER} (out of {len(_equity_gdf)} total)")


def coverage(stops, coverage_radius_m=COVERAGE_RADIUS_M):
    total = 0
    for dguid in DAS_NEAR_ROUTE:
        da = EQUITY_LOOKUP[dguid]
        if any(haversine_m(stop, da["centroid"]) < coverage_radius_m for stop in stops):
            equity_mult = 1.0 + (da["income"] * 0.5) + (da["transit"] * 0.5)
            total += da["population"] * equity_mult
    return total


def averageWalkingDistanceToStop(stops):
    """
    Population-weighted average distance from each DA centroid to its nearest stop.
    """
    if not stops or not DAS_NEAR_ROUTE:
        return 0

    total_weighted_distance = 0
    total_population = 0

    for dguid in DAS_NEAR_ROUTE:
        da = EQUITY_LOOKUP[dguid]
        nearest_dist = min(haversine_m(da["centroid"], stop) for stop in stops)
        total_weighted_distance += nearest_dist * da["population"]
        total_population += da["population"]

    if total_population == 0:
        return 0

    return total_weighted_distance / total_population


# --- POI-based destination bonus ---
POI_TAGS = {
    "amenity": [
        "school", "hospital", "clinic", "college", "university", "library",
        "pharmacy", "community_centre", "social_facility",
        "veterinary", "place_of_worship", "shelter", "food_bank",
        "restaurant",
    ],
    "shop": ["supermarket", "mall", "convenience", "hairdresser", "laundry"],
    "healthcare": ["optometrist", "physiotherapist", "dialysis", "alternative"],
    "leisure": ["sports_centre", "stadium"],
}

VICTORIA_BBOX = {
    "min_lat": 48.35, "max_lat": 48.55,
    "min_lon": -123.6, "max_lon": -123.2,
}


def first_valid(*values):
    for v in values:
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            return v
    return None


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
            # polygons/multipolygons (campuses, hospital grounds, malls, etc.) — use centroid
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x

        poi_type = first_valid(row.get("amenity"), row.get("shop"), row.get("leisure"), row.get("healthcare"))
        name = row.get("name", None)
        records.append({"lat": lat, "lon": lon, "type": poi_type, "name": name})

    print(f"Fetched {len(records)} POIs")
    return records


def load_or_fetch_pois(cache_path="pois.json"):
    if os.path.exists(cache_path):
        print(f"Loading cached POIs from {cache_path}")
        with open(cache_path) as f:
            return json.load(f)
    pois = fetch_pois()
    with open(cache_path, "w") as f:
        json.dump(pois, f, indent=2)
    print(f"Saved {len(pois)} POIs to {cache_path}")
    return pois


POIS = load_or_fetch_pois()


def get_pois_near_route(route_coords, pois, buffer_m=ROUTE_BUFFER_M):
    """
    Pre-filter step, same pattern as get_das_near_route — only keep POIs
    actually near this route's corridor, computed once, not per-individual.
    """
    route_line = LineString([(lon, lat) for lat, lon in route_coords])
    route_gdf = gpd.GeoDataFrame(geometry=[route_line], crs="EPSG:4326").to_crs(DA_CRS_METRIC)
    buffered_route = route_gdf.geometry.iloc[0].buffer(buffer_m)

    poi_points = gpd.GeoDataFrame(
        pois,
        geometry=[Point(p["lon"], p["lat"]) for p in pois],
        crs="EPSG:4326",
    ).to_crs(DA_CRS_METRIC)

    nearby_idx = poi_points.sindex.query(buffered_route, predicate="intersects")
    return [pois[i] for i in nearby_idx]


POIS_NEAR_ROUTE = get_pois_near_route(ROUTE_COORDS, POIS)
print(f"Filtered to {len(POIS_NEAR_ROUTE)} POIs near route {ROUTE_NUMBER} (out of {len(POIS)} total)")

POI_WEIGHT = {
    "hospital": 3,
    "clinic": 2,
    "pharmacy": 2,
    "school": 2,
    "college": 2,
    "university": 2,
    "library": 1,
    "community_centre": 2,
    "social_facility": 3,
    "supermarket": 2,
    "mall": 2,
    "convenience": 1,
    "restaurant": 1,
    "sports_centre": 1,
    "stadium": 1,
    "veterinary": 1,
    "place_of_worship": 1,
    "shelter": 3,
    "food_bank": 3,
    "hairdresser": 1,
    "laundry": 1,
    "optometrist": 1,
    "physiotherapist": 1,
    "dialysis": 3,
    "alternative": 1,
}
POI_RADIUS_M = 400  # same walkability radius as coverage(), for consistency
MAX_DESTINATION_BONUS = 30  # TODO: tune against real observed distribution once GA is running end-to-end


def destination_bonus(stops):
    # For each POI near the route, award bonus once if ANY stop reaches it within POI_RADIUS_M —
    # avoids double-counting the same POI across multiple nearby stops.
    total = 0
    for poi in POIS_NEAR_ROUTE:
        poi_coords = (poi["lat"], poi["lon"])
        is_reachable = any(haversine_m(stop, poi_coords) < POI_RADIUS_M for stop in stops)
        if is_reachable:
            total += POI_WEIGHT.get(poi["type"], 1)  # default weight 1 for unlisted types
    return min(total, MAX_DESTINATION_BONUS)


def estimated_travel_time(stops):
    """
    Penalizes route slowness as stop count grows.
    TODO: replace flat per-stop dwell time with something informed by ridership data
    https://www.bctransit.com/plans-and-projects/service-performance/
    """
    BASE_TRAVEL_TIME_S = 900       # placeholder base route time in seconds
    AVG_DWELL_TIME_S = 20          # placeholder seconds lost per stop (accel/decel + boarding)
    return BASE_TRAVEL_TIME_S + len(stops) * AVG_DWELL_TIME_S


def transfer_bonus(stops):
    """Rewards stops placed near other routes' existing stops (enables transfers)."""
    bonus = 0
    for s in stops:
        if any(haversine_m(s, other) <= GA_CONFIG["transfer_radius_meters"] for other in OTHER_ROUTE_STOPS):
            bonus += 1
    return bonus


def weightFunction(stops):
    fitness = (
        coverage(stops) * WEIGHTS["w_coverage"]
        - averageWalkingDistanceToStop(stops) * WEIGHTS["w_walking_distance"]
        - spacing_penalty(stops) * WEIGHTS["w_spacing_penalty"]
        + destination_bonus(stops) * WEIGHTS["w_destination_bonus"]
        - len(stops) * WEIGHTS["w_cost_per_stop"]
        - estimated_travel_time(stops) * WEIGHTS["w_travel_time"]
        + transfer_bonus(stops) * WEIGHTS["w_transfer"]

        # TODO: print outputs
    )
    return fitness
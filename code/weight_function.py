# GENERAL TODO: 
# choose snake case or camle case
# organize repo: /data for all data, /scripts for helper scripts, /code for code with further organization within it -> /genetic-algorithm, /data-processing, /UI...

import pandas as pd
import geopandas as gpd
import folium
import random
import math

from busRoutes import randomStopsOnRoute, getRouteShape

from config import GA_CONFIG, ROUTE_NUMBER, WEIGHTS


shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")
stop_times = pd.read_csv("stop_times.txt")
stops = pd.read_csv("stops.txt")

# Add these to your existing reads
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

# TODO (later): swap to all other routes instead of the hardcoded three (uncomment next 3 lines and above OTHER_ROUTE_STOPS assignment)
# _all_route_numbers = routes["route_short_name"].unique().tolist()
# _other_route_numbers = [r for r in _all_route_numbers if str(r) != str(ROUTE_NUMBER)]
# OTHER_ROUTE_STOPS = get_stops_for_routes(_other_route_numbers, routes, trips, stop_times, stops)

# distance formula for lat and longs
def haversine_m(p1, p2):
    """Distance in meters between two (lat, lon) points."""
    R = 6371000
    lat1, lon1 = map(math.radians, p1)
    lat2, lon2 = map(math.radians, p2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))


def is_feasible(point, routeCoords):
    """
    Hard feasibility check for a candidate stop.
    TODO (low priority): replace placeholder logic with real checks:
      - distance to nearest road-network edge under some threshold
      - not within X meters of a highway/off-ramp segment
      - not on private property / restricted zone if that data is available
    Returns True/False.
    """
    return True  # stub — always feasible until real road/geometry data is wired in


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

    # Variable stop count: pick a random target size within the configured range
    target_count = random.randint(GA_CONFIG["min_stops"], GA_CONFIG["max_stops"])

    for rNum, coords, color in routeShapes:
        candidate_stops = randomStopsOnRoute(coords, target_count)

        # Reject-and-resample for feasibility (simple version: filter, don't loop-retry yet)
        candidate_stops = [s for s in candidate_stops if is_feasible(s, coords)]

        #TODO: Should make it so that if we drop stops, we add more so that we dont end up with less than target_count stops. For now, just accept that we might have less than target_count stops.
        # Hard spacing constraint applied at construction time
        candidate_stops = enforce_min_spacing(candidate_stops, GA_CONFIG["min_spacing_meters"])

        stops = candidate_stops
        routeNumber = rNum

    return {"routeNumber": routeNumber,  "stops": stops}


# TODO: Should probably normalize this to 0-1, idk if normalize input our output would be better
def weightFunction(stops):
    fitness = (
        # coverage(stops) * WEIGHTS["w_coverage"]
        - averageWalkingDistanceToStop(stops) * WEIGHTS["w_walking_distance"]
        - spacing_penalty(stops) * WEIGHTS["w_spacing_penalty"]
        + destination_bonus(stops) * WEIGHTS["w_destination_bonus"]
        - len(stops) * WEIGHTS["w_cost_per_stop"]
        - estimated_travel_time(stops) * WEIGHTS["w_travel_time"]
        + transfer_bonus(stops) * WEIGHTS["w_transfer"]
    )
    return fitness


# One-time setup, similar to OTHER_ROUTE_STOPS — compute once, not per-generation
import geopandas as gpd

def build_equity_lookup(geojson_path):
    # Load your processed data
    gdf = gpd.read_file(geojson_path)
    
    # Create a dictionary: DGUID -> {pop, income_norm, transit_norm}
    # This makes looking up equity data by ID lightning fast during the GA loop
    lookup = {
        row["DGUID"]: {
            "pop": row["population"],
            "income": row["pct_low_income_norm"],
            "transit": row["pct_transit_commute_mode_norm"]
        }
        for _, row in gdf.iterrows()
    }
    return lookup

# --- Implementation ---
# Use the file you just generated
EQUITY_LOOKUP = build_equity_lookup("victoria_equity_data.geojson")

# may look confusing - build_equity_lookup + coverage() combines weighting low-income/transit_commute_mode_norm norms with population density.
# This approach is fine for living areas etc, but in places where people still need transit even if they aren't low income like to bars venues or sports arenas, 
# those won't get a fair bonus here. That must be logically captured by POIS or something else - else split coverage() into raw pop density, and include secondary
# equity bias bonus. TODO^
# TODO: getting into scope creep here...maybe just pop dens no income / transit method stuff. but : need to precalculate DA centroids because in the loops extremely slow
# pre-filter DAs near route.
# perhaps include weights for incom and transit as genes themselves instead of fixed at 0.5.
# use sindex from gdf if for da in DAs_near_route is slow.
def coverage(stops, COVERAGE_RADIUS_M=400):
    total = 0
    for da in DAs_near_route: # Assuming DAs_near_route is a list/GeoDataFrame
        # 1. Check if ANY stop in the proposed route covers this DA
        is_covered = any(haversine_m(stop, da_centroid(da)) < COVERAGE_RADIUS_M for stop in stops)
        
        if is_covered:
            # 2. Retrieve equity data for this DA
            # If the DA is missing from our lookup, default to zero impact (or 1.0 if you prefer)
            equity_data = EQUITY_LOOKUP.get(da["DGUID"], {"income": 0, "transit": 0})
            
            # 3. Calculate dynamic weight
            # Combine income and transit into a single multiplier (e.g., 0-2 range)
            # Higher score = higher priority
            equity_mult = 1.0 + (equity_data["income"] * 0.5) + (equity_data["transit"] * 0.5)
            
            # 4. Add weighted population to total
            total += da["population"] * equity_mult
            
    return total


def spacing_penalty(stops):
    # NOTE: hard min-spacing is now enforced at generation time (enforce_min_spacing).
    # This soft penalty can instead reward *even* spacing rather than just minimum spacing —
    # e.g. penalize high variance in gap distances between consecutive stops.
    return -1


def destination_bonus(stops):
    # TODO: manual/curated list of POIs (schools, hospitals, grocery, malls) with (lat, lon).
    # For each stop, sum bonus for POIs within some radius, e.g.:
    # sum(POI_WEIGHT[poi.type] for poi in POIS if haversine_m(stop, poi.coords) < POI_RADIUS)
    return -1


def averageWalkingDistanceToStop(stops):
    # TODO: for each population point/DA centroid, distance to nearest stop; average across DAs.
    return -1


def estimated_travel_time(stops):
    """
    NEW: penalizes route slowness as stop count grows.
    TODO: replace flat per-stop dwell time with something informed by ridership data https://www.bctransit.com/plans-and-projects/service-performance/ SEE THE MD.
    """
    BASE_TRAVEL_TIME_S = 900       # placeholder base route time in seconds
    AVG_DWELL_TIME_S = 20          # placeholder seconds lost per stop (accel/decel + boarding)
    return BASE_TRAVEL_TIME_S + len(stops) * AVG_DWELL_TIME_S


def transfer_bonus(stops):
    """
    NEW: rewards stops placed near other routes' existing stops (enables transfers).
    """
    bonus = 0
    for s in stops:
        if any(haversine_m(s, other) <= GA_CONFIG["transfer_radius_meters"] for other in OTHER_ROUTE_STOPS):
            bonus += 1
    return bonus


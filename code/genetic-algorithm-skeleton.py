import pandas as pd
import folium
import random
import math

from busRoutes import randomStopsOnRoute, getRouteShape


GA_CONFIG = {
    # Genetic algorithm hyper-parameters
    "num_generations": 200,
    "num_parents_mating": 10,

    "min_stops": 5,                 # variable stop count
    "max_stops": 30,

    "min_spacing_meters": 200,      # hard anti-clustering constraint
    "transfer_radius_meters": 100,  # for connectivity bonus
}

ROUTE_NUMBER = 95

WEIGHTS = {
    "w_coverage": 1,
    "w_walking_distance": 1,
    "w_spacing_penalty": 1,
    "w_destination_bonus": 1,
    "w_cost_per_stop": 1,    #cost of stop count
    "w_travel_time": 1,      #route slowdown
    "w_transfer": 1,         #proximity to other routes' stops
}

shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")

# Precompute once, not per-generation — used by transfer/connectivity bonus
# TODO: populate this from other routes' stop data (GTFS stops.txt filtered to routes != ROUTE_NUMBER)
OTHER_ROUTE_STOPS = []  # List of (lat, lon)

# distance formula
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
    TODO: replace placeholder logic with real checks:
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


def randomlyGenerateBusStops(routeNumber: int, generationNumber: int):
    routeShapes = getRouteShape(routeNumber, routes, trips, shapes)

    stops = []

    # Variable stop count: pick a random target size within the configured range
    target_count = random.randint(GA_CONFIG["min_stops"], GA_CONFIG["max_stops"])

    for rNum, coords, color in routeShapes:
        candidate_stops = randomStopsOnRoute(coords, target_count)

        # Reject-and-resample for feasibility (simple version: filter, don't loop-retry yet)
        candidate_stops = [s for s in candidate_stops if is_feasible(s, coords)]

        # Hard spacing constraint applied at construction time
        candidate_stops = enforce_min_spacing(candidate_stops, GA_CONFIG["min_spacing_meters"])

        stops = candidate_stops
        routeNumber = rNum

    return {"routeNumber": routeNumber, "generationNumber": generationNumber, "stops": stops}


def weightFunction(stops):
    fitness = (
        coverage(stops) * WEIGHTS["w_coverage"]
        - averageWalkingDistanceToStop(stops) * WEIGHTS["w_walking_distance"]
        - spacing_penalty(stops) * WEIGHTS["w_spacing_penalty"]
        + destination_bonus(stops) * WEIGHTS["w_destination_bonus"]
        - len(stops) * WEIGHTS["w_cost_per_stop"]
        - estimated_travel_time(stops) * WEIGHTS["w_travel_time"]
        + transfer_bonus(stops) * WEIGHTS["w_transfer"]
    )
    return fitness


def coverage(stops):
    # TODO: population coverage, weighted by equity multiplier per DA.
    # weighted_coverage = sum(population_in_da * equity_multiplier(DA) for DA in DAs_within_radius(stops))
    # equity_multiplier() should pull from census DA-level income/no-vehicle-household data
    return -1


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
    TODO: replace flat per-stop dwell time with something informed by ridership data if available.
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


def parentsMate():
    return [()]


def mutateChild():
    return ()


randomlyGeneratedBusStops = []  # List of dicts {"routeNumber": int, "generationNumber": int, "stops": List of (lat, lon)}

for generationNumber in range(GA_CONFIG["num_generations"]):
    randomlyGeneratedBusStops.append(randomlyGenerateBusStops(ROUTE_NUMBER, generationNumber))

print(len(randomlyGeneratedBusStops))

for busStopInfo in randomlyGeneratedBusStops:
    fitnessScore = weightFunction(busStopInfo["stops"])
    busStopInfo["fitness"] = fitnessScore

for busStopInfo in randomlyGeneratedBusStops:
    print(f"Generation {busStopInfo['generationNumber']} - Fitness: {busStopInfo['fitness']:.2f}")
import pandas as pd
import folium
import random
import math

from busRoutes import randomStopsOnRoute, getRouteShape


GA_CONFIG = {
    # Genetic algorithm hyper-parameters
    "num_generations": 200,
    "num_parents_mating": 10,
 
    "num_stops_to_place": 20,       # k stops to select per route
}

ROUTE_NUMBER = 95


WEIGHTS = {
    "w1_walking_distance": 1
}
shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")


def randomlyGenerateBusStops(routeNumber: int, generationNumber: int):
    routeShapes = getRouteShape(routeNumber, routes, trips, shapes)

    stops = []

    for routeNumber, coords, color in routeShapes:

        stops = randomStopsOnRoute(coords, GA_CONFIG["num_stops_to_place"])
       
    return {"routeNumber": routeNumber, "generationNumber": generationNumber, "stops": stops}


def weightFunction():
    return averageWalkingDistanceToStop() * WEIGHTS["w1_walking_distance"]

def averageWalkingDistanceToStop():
    return random.random() * 10

def parentsMate():
    return [()]

def mutateChild():
    return ()


randomlyGeneratedBusStops = [] # Structure: List of dicts {"routeNumber": int, "generationNumber": int, "stops": List of (lat, lon)}

for generationNumber in range(GA_CONFIG["num_generations"]):
   randomlyGeneratedBusStops.append(randomlyGenerateBusStops(ROUTE_NUMBER, generationNumber))


print(len(randomlyGeneratedBusStops))


for busStopInfo in randomlyGeneratedBusStops:
    eval = weightFunction()
    busStopInfo["fitness"] = eval

for busStopInfo in randomlyGeneratedBusStops:
    print(f"Generation {busStopInfo['generationNumber']} - Fitness: {busStopInfo['fitness']:.2f}")
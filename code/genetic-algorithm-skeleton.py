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
    "w1_coverage": 1,
    "w2_walking_distance": 1,
    "w3_spacing_penalty": 1,
    "w4_destination_bonus": 1,
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

    fitness = (
        coverage() * WEIGHTS["w1_coverage"]
        - averageWalkingDistanceToStop() * WEIGHTS["w2_walking_distance"]
        - spacing_penalty() * WEIGHTS["w3_spacing_penalty"]
        + destination_bonus() * WEIGHTS["w4_destination_bonus"]
    )
    return fitness

def coverage():
    # population coverage. set some var for some radius where population is either, "within or outside of" coverage.
    # compute: number of people inside radius return thah bih

    return -1

def spacing_penalty():
    # compute penalty to give for stops too close together?

    return -1

def destination_bonus():
    # this will maybe be a manual list of places/stores/POIs/etc stored in some struct s.t. radius of it to a bus stop can be computed.

    return -1

def averageWalkingDistanceToStop():
    # get pop density
    # get line representing bus line
    # perform calculations for num metres walking to bus stop #some bias under some dist that makes it unneccessary to include
    # return average walking distance to this stop
    return -1

def parentsMate():
    return [()]

def mutateChild():
    return ()


randomlyGeneratedBusStops = [] # Structure: List of dicts {"routeNumber": int, "generationNumber": int, "stops": List of (lat, lon)}

for generationNumber in range(GA_CONFIG["num_generations"]):
   randomlyGeneratedBusStops.append(randomlyGenerateBusStops(ROUTE_NUMBER, generationNumber))


print(len(randomlyGeneratedBusStops))


for busStopInfo in randomlyGeneratedBusStops:
    fitnessScore = weightFunction()
    busStopInfo["fitness"] = fitnessScore

for busStopInfo in randomlyGeneratedBusStops:
    print(f"Generation {busStopInfo['generationNumber']} - Fitness: {busStopInfo['fitness']:.2f}")



    # TODO: add param to vary amount of stops with cost? Travel time / route efficiency penalty? equity (low income households, etc)? infeasible stops? transfer/connectivity bonus? existing infra reuse bonus? any hard constraints e.g., alkl 20 stops clustered at one high densitypoint
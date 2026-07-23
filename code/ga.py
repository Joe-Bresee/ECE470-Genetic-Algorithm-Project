from weight_function import randomlyGenerateBusStops, weightFunction, haversine_m, buildRouteContext
# from config import GA_CONFIG, ROUTE_NUMBER, WEIGHTS
from config import GA_CONFIG, WEIGHTS, ROUTE_NUMBERS
import random
random.seed(42)
import math
import folium
import pandas as pd
from evenlySpacedBusStops import getPoints
from busRoutes import randomStopsOnRoute, getRouteShape


def createInitialPopulation(routeNumber):

    randomlyGeneratedBusStops = []  # List of dicts {"routeNumber": int, "stops": List of (lat, lon)}

    for _ in range(GA_CONFIG["initial_population_size"]):
        randomlyGeneratedBusStops.append(randomlyGenerateBusStops(routeNumber))

    return randomlyGeneratedBusStops

def evaluatePopulation(population, routeContext):
    for busStopInfo in population: 
        fitnessScore = weightFunction(busStopInfo["stops"], routeContext, False)
        busStopInfo["fitness"] = fitnessScore
    return population

def selectParents(population):

    parents = []

    for _ in range(GA_CONFIG["num_parents_mating"]):
        parent = tournamentSelection(population)
        parents.append(parent)

    return parents

# This is just one way to choose parents, once weights are normalized, we could use probabilistic selection based on weights
def tournamentSelection(population, tournament_size=3):
    tournament = random.sample(population, tournament_size)
    best = max(tournament, key=lambda x: x["fitness"])
    return best

def crossover(parents):
    
    generatedChildren = []
    
    while len(generatedChildren) < GA_CONFIG["desired_population_size"]:

        parent1, parent2 = random.sample(parents, 2)  # Randomly select two parents

        child = crossoverTwoParents(parent1, parent2)
        generatedChildren.append(child)

    return generatedChildren
        

def crossoverTwoParents(parent1, parent2):
        
    if parent1["routeNumber"] != parent2["routeNumber"]:
        raise ValueError("Parents must have the same route number for crossover.")

    crossover_point = random.randint(
        1,
        min(len(parent1["stops"]), len(parent2["stops"])) - 1
    )

    child_stops = (
        parent1["stops"][:crossover_point]
        +
        parent2["stops"][crossover_point:]
    )

    return {
        "routeNumber": parent1["routeNumber"],
        "stops": child_stops,
        "fitness": None
    }

def mutate(child, candidate_stops, sigma=300.0): # sigma properly tuned in meters
    stops = child["stops"]
    if not stops:
        return child
    
    idxToMutate = random.randrange(len(stops))
    oldStop = stops[idxToMutate]

    # Use haversine_m so distances are strictly in meters, matching sigma
    distances = [haversine_m(oldStop, candidate) for candidate in candidate_stops]

    weights = [math.exp(-d**2 / (2 * sigma**2)) for d in distances]
    newStop = random.choices(candidate_stops, weights=weights, k=1)[0]

    newStops = stops.copy()
    newStops[idxToMutate] = newStop

    return {
        "routeNumber": child["routeNumber"],
        "stops": newStops,
        "fitness": None
    }


def createNextGeneration(population, candidate_stops, sigma):

    parents = selectParents(population)

    children = crossover(parents)

    mutatedChildren = []

    for child in children:
        if random.random() < GA_CONFIG["mutation_probability"]:
            child = mutate(child, candidate_stops, sigma)
        mutatedChildren.append(child)

    return mutatedChildren  



def getBestIndividual(population):
    best = population[0]
    for individual in population:
        if individual["fitness"] > best["fitness"]:
            best = individual

    return best

def getWorstIndividual(population):
    worst = population[0]
    for individual in population:
        if individual["fitness"] < worst["fitness"]:
            worst = individual

    return worst


def populationDiversity(population):

    unique = set()

    for individual in population:
        unique.add(tuple(individual["stops"]))

    return len(unique)


# def mapBusStops(stops, routeNumber):
#     avg_lat = sum(lat for lat, lon in stops) / len(stops)
#     avg_lon = sum(lon for lat, lon in stops) / len(stops)

#     m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

#     ROUTE_NUMBERS = [95]

#     shapes = pd.read_csv("shapes.txt")
#     routes = pd.read_csv("routes.txt")
#     trips = pd.read_csv("trips.txt")

#     for otherRouteNumber in ROUTE_NUMBERS:
#         routeShapesForThis = getRouteShape(otherRouteNumber, routes, trips, shapes)
#         for rNum, coords, color in routeShapesForThis:
#             folium.PolyLine(
#                 coords,
#                 color=color,
#                 weight=5,
#                 tooltip=f"Route {rNum}"
#             ).add_to(m)

#     for lat, lon in stops:
#         folium.CircleMarker(
#             location=[lat, lon],
#             radius=6,
#             color="blue",
#             fill=True,
#             fill_color="white",
#             fill_opacity=1,
#             tooltip=f"Route {routeNumber} stop"
#         ).add_to(m)

#     return m

def mapBusStops(bestPerRoute):
    all_stops = [stop for individual in bestPerRoute for stop in individual["stops"]]
    avg_lat = sum(lat for lat, lon in all_stops) / len(all_stops)
    avg_lon = sum(lon for lat, lon in all_stops) / len(all_stops)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

    shapes = pd.read_csv("shapes.txt")
    routes = pd.read_csv("routes.txt")
    trips = pd.read_csv("trips.txt")

    colors = ["blue", "red", "green", "purple"]  # cycle if you have >4 routes

    for i, individual in enumerate(bestPerRoute):
        routeNumber = individual["routeNumber"]
        color = colors[i % len(colors)]

        routeShapesForThis = getRouteShape(routeNumber, routes, trips, shapes)
        for rNum, coords, shapeColor in routeShapesForThis:
            folium.PolyLine(
                coords,
                color=color,
                weight=5,
                tooltip=f"Route {rNum}"
            ).add_to(m)

        for lat, lon in individual["stops"]:
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=color,
                fill=True,
                fill_color="white",
                fill_opacity=1,
                tooltip=f"Route {routeNumber} stop"
            ).add_to(m)

    return m

# def runGeneticAlgorithmForRoute(routeNumber):

#     print("getting candidate spots")

#     candidateSpots, sigma = getPoints(routeNumber)

#     print("Creating popoulation")

#     # This is the initial population
#     population = createInitialPopulation()

#     # Currently doing a fixed number of generations, but we could also do a convergence check
#     # Once the weight function is better, we will switch
#     for generation in range(GA_CONFIG["num_generations"]):
#         print(f"Generation {generation + 1}/{GA_CONFIG['num_generations']}")

#         evaluatedPopulation = evaluatePopulation(population)

#         bestIndividual = getBestIndividual(evaluatedPopulation)
#         worstIndividual = getWorstIndividual(evaluatedPopulation)

#         weightFunction(bestIndividual["stops"], verbose=True)
#         weightFunction(worstIndividual["stops"], verbose=True)

#         print(f"Best individual fitness: {bestIndividual['fitness']:.7f}")
#         # print(f"Worst individual fitness: {worstIndividual['fitness']:.2f}")
#         # print(f"Population diversity: {populationDiversity(evaluatedPopulation)}")
#         population  = createNextGeneration(evaluatedPopulation, candidateSpots, sigma)

#     mapBusStops(bestIndividual["stops"], bestIndividual["routeNumber"]).save("best_bus_stops.html")


def runGeneticAlgorithmForRoute(routeNumber):

    print("Route context")

    routeContext = buildRouteContext(routeNumber, ROUTE_NUMBERS)
    
    print("getting candidate spots")

    candidateSpots, sigma = getPoints(routeNumber)

    print("Getting population")

    population = createInitialPopulation(routeNumber)

    for generation in range(GA_CONFIG["num_generations"]):
        evaluatedPopulation = evaluatePopulation(population, routeContext)
        bestIndividual = getBestIndividual(evaluatedPopulation)
        weightFunction(bestIndividual["stops"], routeContext, verbose=True)
        population = createNextGeneration(evaluatedPopulation, candidateSpots, sigma)

    return bestIndividual
   

def runGeneticAlgorithm():
    bestPerRoute = []
    for routeNumber in ROUTE_NUMBERS:
        print("Working on route number", routeNumber)
        best = runGeneticAlgorithmForRoute(routeNumber)
        bestPerRoute.append(best)

    mapBusStops(bestPerRoute).save("best_bus_stops.html")


runGeneticAlgorithm()


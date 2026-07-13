from weight_function import randomlyGenerateBusStops, weightFunction
from config import GA_CONFIG, ROUTE_NUMBER, WEIGHTS
import random
import math
import folium
import pandas as pd
from evenlySpacedBusStops import getPoints


def createInitialPopulation():

    randomlyGeneratedBusStops = []  # List of dicts {"routeNumber": int, "stops": List of (lat, lon)}

    for _ in range(GA_CONFIG["initial_population_size"]):
        randomlyGeneratedBusStops.append(randomlyGenerateBusStops(ROUTE_NUMBER))

    return randomlyGeneratedBusStops

def evaluatePopulation(population):
    for busStopInfo in population: 
        fitnessScore = weightFunction(busStopInfo["stops"])
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

def segmentLength(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


# We should actually pass in a proper sigma value, rn its hardcoded
def mutate(child, candidate_stops, sigma=0.195424042632881): 

    stops = child["stops"]
    idxToMutate = random.randrange(len(stops))
    oldStop = stops[idxToMutate]

    distances = [segmentLength(oldStop, candidate) for candidate in candidate_stops]

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

    return children



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


def mapBusStops(stops, routeNumber):
    
    # Center map around average stop location
    avg_lat = sum(lat for lat, lon in stops) / len(stops)
    avg_lon = sum(lon for lat, lon in stops) / len(stops)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=13
    )

        

    ROUTE_NUMBERS = [95, 26]


    shapes = pd.read_csv("shapes.txt")
    routes = pd.read_csv("routes.txt")
    trips = pd.read_csv("trips.txt")

    # Collect all shapes first to center the map properly
    allCoords = []
    routeShapes = []


    for i, routeNumber in enumerate(ROUTE_NUMBERS):
        route = routes[routes["route_short_name"] == str(routeNumber)]
        routeId = route["route_id"].iloc[0]
        routeColor = route["route_color"].iloc[0]

        routeTrips = trips[trips["route_id"] == routeId]
        shape_id = routeTrips.iloc[0]["shape_id"]

        shape = shapes[shapes["shape_id"] == shape_id].sort_values("shape_pt_sequence")

        coords = list(zip(shape["shape_pt_lat"], shape["shape_pt_lon"]))
        allCoords.extend(coords)
        routeShapes.append((routeNumber, coords, f"#{routeColor}"))


        for routeNumber, coords, color in routeShapes:
            folium.PolyLine(
                coords,
                color=color,
                weight=5,
                tooltip=f"Route {routeNumber}"
            ).add_to(m)

    for lat, lon in stops:
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color="blue",
            fill=True,
            fill_color="white",
            fill_opacity=1,
            tooltip=f"Route {routeNumber} stop"
        ).add_to(m)

    return m

def runGeneticAlgorithm():

    candidateSpots, sigma = getPoints(GA_CONFIG["NUM_EVENLY_SPACED_POINTS"])  # Get candidate spots and sigma from evenly spaced points

    # This is the initial population
    population = createInitialPopulation()

    # Currently doing a fixed number of generations, but we could also do a convergence check
    # Once the weight function is better, we will switch
    for generation in range(GA_CONFIG["num_generations"]):
        print(f"Generation {generation + 1}/{GA_CONFIG['num_generations']}")

        evaluatedPopulation = evaluatePopulation(population)

        bestIndividual = getBestIndividual(evaluatedPopulation)
        worstIndividual = getWorstIndividual(evaluatedPopulation)

        print(f"Best individual fitness: {bestIndividual['fitness']:.7f}")
        # print(f"Worst individual fitness: {worstIndividual['fitness']:.2f}")
        # print(f"Population diversity: {populationDiversity(evaluatedPopulation)}")
        population  = createNextGeneration(evaluatedPopulation, candidateSpots, sigma)

    mapBusStops(bestIndividual["stops"], bestIndividual["routeNumber"]).save("best_bus_stops.html")

    print(f"Best bus stops saved to best_bus_stops.html with fitness: {bestIndividual['fitness']:.7f}")

   
runGeneticAlgorithm()



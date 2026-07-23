GA_CONFIG = {
    # Genetic algorithm hyper-parameters
    'initial_population_size': 100,
    # 'initial_population_size': 1000,

    'desired_population_size': 100,
    # 'desired_population_size': 1000,

    "num_generations": 100,
    # "num_generations": 100,

    "num_parents_mating": 30,
    # "num_parents_mating": 300,
    "mutation_probability": 0.8,  # Probability of mutation for each child

    "min_stops": 25,                 # variable stop count
    "max_stops": 30,

    "min_spacing_meters": 200,      # hard anti-clustering constraint
    "transfer_radius_meters": 100,  # for connectivity bonus

    "NUM_EVENLY_SPACED_POINTS": 200,  # Number of evenly spaced points to generate along the route, this is used for mutations
}

# ROUTE_NUMBER = 95

ROUTE_NUMBERS = [95, 14, 26]

WEIGHTS = {
    "w_coverage": 10,           # equity-weighted population coverage, in [0,1]
    "w_walking_distance": 1,    # walksheds-from-ideal, typically 1-5
    "w_spacing_penalty": 3,     # dimensionless unevenness, typically 0.01-0.5
    "w_destination_bonus": 15,  # fraction of reachable POI value, in [0,1]
    "w_cost_per_stop": 2,       # normalized stop count, in [0,1]
    "w_travel_time": 1,         # route duration in hours, typically 2-4
    "w_transfer": 5,            # fraction of stops enabling transfer, in [0,1]
}
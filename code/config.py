GA_CONFIG = {
    # Genetic algorithm hyper-parameters
    'initial_population_size': 100,
    # 'initial_population_size': 1000,

    'desired_population_size': 100,
    # 'desired_population_size': 1000,

    "num_generations": 20,
    # "num_generations": 100,

    "num_parents_mating": 30,
    # "num_parents_mating": 300,
    "mutation_probability": 0.8,  # Probability of mutation for each child

    "min_stops": 20,                 # variable stop count
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
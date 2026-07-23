# Public Transit Stop Placer

Quinn Webster, Joe Bresee, Scott Garneau

This project explores how to place bus stops for a transit route in a way that improves rider access without making the stop spacing unrealistic. The goal is to find a stop layout that balances coverage, walking distance, transfer opportunities, and proximity to useful destinations.

The implementation uses a genetic algorithm. It starts from candidate stop locations along a route, evaluates each candidate layout with a weighted fitness function, and then iteratively evolves better stop sets over multiple generations.

## What the project is trying to do

For a chosen transit route, the script aims to place stops that:

- improve access for nearby residents and equity-weighted populations
- keep stops reasonably spaced along the route
- support transfers to other routes
- stay close to important destinations such as schools, clinics, supermarkets, and community facilities

The result is a set of stop locations that can be viewed as an interactive map.

## How it works

1. Load route and transit data from the project’s GTFS-style text files.
2. Generate initial candidate stop layouts along the route.
3. Score each layout using a custom fitness function based on several weighted criteria.
4. Apply genetic algorithm steps:
   - select strong parent layouts
   - combine them through crossover
   - mutate some children to explore new stop positions
5. Keep the best-performing layout and save it as an HTML map.

## Project structure

- `code/ga.py` — main genetic algorithm workflow
- `code/weight_function.py` — fitness scoring and spatial evaluation logic
- `code/config.py` — GA parameters and route settings
- `code/busRoutes.py` — route and stop generation helpers
- `code/evenlySpacedBusStops.py` — candidate stop generation logic
- `code/plot_actual_stops.py` and `code/best_bus_stops.html` — map-related output examples

## Setup

From the project root, install the required Python packages:

```bash
pip install -r requirements.txt
```

If you run into missing geospatial packages, install them as well:

```bash
pip install geopandas osmnx shapely
```

## Run the optimizer

The script expects to be run from the `code` directory because it reads data files relative to that location:

```bash
cd code
python ga.py
```

This will print generation-by-generation progress and save the best result to:

```bash
code/best_bus_stops.html
```

## Notes

- The current configuration targets route 95 by default. You can change this in `code/config.py`.
- The fitness function is intentionally weighted and can be adjusted depending on what matters most for the route being studied.

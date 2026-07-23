"""
Generates two random parent bus stop layouts, plots them in different
colors (blue = parent 1, pink = parent 2), then performs crossover and
plots the child with each stop colored by which parent it came from.

Reuses:
  - randomlyGenerateBusStops()  (weight_function.py)
  - crossoverTwoParents()       (ga.py)
  - getRouteShape()             (busRoutes.py)

NOTE: ga.py currently calls runGeneticAlgorithm() unconditionally at the
bottom of the file. Guard it before running this script:

    if __name__ == "__main__":
        runGeneticAlgorithm()

Run from the code/ directory (same as ga.py) since data paths are relative.
"""

import random
random.seed(42)

import folium
import pandas as pd

from config import ROUTE_NUMBER
from weight_function import randomlyGenerateBusStops
from busRoutes import getRouteShape
from ga import crossoverTwoParents

PARENT1_COLOR = "blue"
PARENT2_COLOR = "deeppink"


def _baseMap(routeNumber, routes, trips, shapes):
    """Same base-map setup as mapBusStops() in ga.py, minus the stop markers."""
    rNum, coords, color = getRouteShape(routeNumber, routes, trips, shapes)[0]
    avg_lat = sum(lat for lat, lon in coords) / len(coords)
    avg_lon = sum(lon for lat, lon in coords) / len(coords)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
    folium.PolyLine(coords, color="gray", weight=4, tooltip=f"Route {rNum}").add_to(m)
    return m


def mapParentsAndChild(parent1, parent2, child, childColors, outPrefix="crossover_demo"):
    shapes = pd.read_csv("shapes.txt")
    routes = pd.read_csv("routes.txt")
    trips = pd.read_csv("trips.txt")

    # --- Parent 1 map ---
    parent1Map = _baseMap(ROUTE_NUMBER, routes, trips, shapes)

    for lat, lon in parent1["stops"]:
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=PARENT1_COLOR,
            fill=True, fill_color=PARENT1_COLOR, fill_opacity=1,
            tooltip="Parent 1 stop"
        ).add_to(parent1Map)

    parent1Map.save(f"{outPrefix}_parent1.html")

    # --- Parent 2 map ---
    parent2Map = _baseMap(ROUTE_NUMBER, routes, trips, shapes)

    for lat, lon in parent2["stops"]:
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=PARENT2_COLOR,
            fill=True, fill_color=PARENT2_COLOR, fill_opacity=1,
            tooltip="Parent 2 stop"
        ).add_to(parent2Map)

    parent2Map.save(f"{outPrefix}_parent2.html")

    # --- Child map ---
    childMap = _baseMap(ROUTE_NUMBER, routes, trips, shapes)

    for (lat, lon), c in zip(child["stops"], childColors):
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=c,
            fill=True, fill_color=c, fill_opacity=1,
            tooltip="Child stop (inherited)"
        ).add_to(childMap)

    childMap.save(f"{outPrefix}_child.html")

    print(
        f"Saved {outPrefix}_parent1.html, {outPrefix}_parent2.html, "
        f"and {outPrefix}_child.html"
    )


def getChildColors(parent1, parent2, child):
    """Color each child stop by which parent it's positionally inherited
    from — child stops before the crossover point match parent1 exactly,
    stops after match parent2, so equality check recovers the split."""
    colors = []
    for i, stop in enumerate(child["stops"]):
        if i < len(parent1["stops"]) and stop == parent1["stops"][i]:
            colors.append(PARENT1_COLOR)
        else:
            colors.append(PARENT2_COLOR)
    return colors


def main():
    parent1 = randomlyGenerateBusStops(ROUTE_NUMBER)
    parent2 = randomlyGenerateBusStops(ROUTE_NUMBER)

    child = crossoverTwoParents(parent1, parent2)
    childColors = getChildColors(parent1, parent2, child)

    mapParentsAndChild(parent1, parent2, child, childColors)


if __name__ == "__main__":
    main()
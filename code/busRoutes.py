import pandas as pd
import random
import math


def getRouteShape(routeNumber, routes, trips, shapes):

    allCoords = []
    routeShapes = []

    route = routes[routes["route_short_name"] == str(routeNumber)]
    routeId = route["route_id"].iloc[0]
    routeColor = route["route_color"].iloc[0]

    routeTrips = trips[trips["route_id"] == routeId]
    shape_id = routeTrips.iloc[0]["shape_id"]

    shape = shapes[shapes["shape_id"] == shape_id].sort_values("shape_pt_sequence")

    coords = list(zip(shape["shape_pt_lat"], shape["shape_pt_lon"]))
    allCoords.extend(coords)
    routeShapes.append((routeNumber, coords, f"#{routeColor}"))

    return routeShapes


def segmentLength(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def randomStopsOnRoute(coords, numStops):

    # Calculate length of each segment
    segments = []
    lengths = []
    for i in range(len(coords) - 1):
        segments.append((coords[i], coords[i+1]))
        lengths.append(segmentLength(coords[i], coords[i+1]))
    
    totalLength = sum(lengths)
    weights = [l / totalLength for l in lengths]  # probability per segment

    stops = []
    for _ in range(numStops):
        # Pick a segment, weighted by length
        chosen = random.choices(segments, weights=weights, k=1)[0]
        
        # Interpolate randomly within that segment
        t = random.random()
        lat = chosen[0][0] + t * (chosen[1][0] - chosen[0][0])
        lon = chosen[0][1] + t * (chosen[1][1] - chosen[0][1])
        
        stops.append((lat, lon))
    
    return stops


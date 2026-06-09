import pandas as pd
import folium
import random
import math

ROUTE_NUMBERS = [95, 26]
NUMBER_OF_STOPS = 50


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


# Center map on the average of ALL route points
center_lat = sum(c[0] for c in allCoords) / len(allCoords)
center_lon = sum(c[1] for c in allCoords) / len(allCoords)

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

for routeNumber, coords, color in routeShapes:
    folium.PolyLine(
        coords,
        color=color,
        weight=5,
        tooltip=f"Route {routeNumber}"
    ).add_to(m)

    stops = randomStopsOnRoute(coords, NUMBER_OF_STOPS)

    for lat, lon in stops:
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color=color,
            fill=True,
            fill_color="white",
            fill_opacity=1,
            tooltip=f"Route {routeNumber} stop"
        ).add_to(m)


# This shows the coordinates that makes up a bus route
# for routeNumber, coords, color in routeShapes:
#     for lat, lon in coords:
#         folium.CircleMarker(location=[lat, lon], radius=3, color=color).add_to(m)


# stops = pd.read_csv("stops.txt")
# stop_times = pd.read_csv("stop_times.txt")

# stopCoords = stops[["stop_lat", "stop_lon"]].values.tolist()

# print(stopCoords)

# for lat, lon in stopCoords:
#     folium.CircleMarker(location=[lat, lon], radius=3, color="black").add_to(m)

m.save("routes.html")
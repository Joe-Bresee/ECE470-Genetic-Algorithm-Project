import pandas as pd
import folium

shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")

routeNumbers = [95, 26]

# Collect all shapes first to center the map properly
allCoords = []
routeShapes = []

for i, routeNumber in enumerate(routeNumbers):
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

# Draw each route
for routeNumber, coords, color in routeShapes:
    folium.PolyLine(
        coords,
        color=color,
        weight=5,
        tooltip=f"Route {routeNumber}"  # shows route number on hover
    ).add_to(m)

# for routeNumber, coords, color in routeShapes:
#     for lat, lon in coords:
#         folium.CircleMarker(location=[lat, lon], radius=3, color=color).add_to(m)


m.save("routes.html")
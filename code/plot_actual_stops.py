import pandas as pd
import folium
from busRoutes import getRouteShape

ROUTE_NUMBERS = [95, 14, 26]

shapes = pd.read_csv("shapes.txt")
routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")
stop_times = pd.read_csv("stop_times.txt")
stops = pd.read_csv("stops.txt")

COLORS = ["blue", "red", "green", "purple"]


def get_stops_for_route(route_number, routes_df, trips_df, stop_times_df, stops_df, direction_id=0):
    """Get the actual GTFS stop coordinates for a single route, one direction only
    (as scheduled, not GA-generated). GTFS routes normally have trips running both
    ways, so without this filter you get both directions' stops overlaid."""
    route_number_str = str(route_number)
    route_ids = routes_df[routes_df["route_short_name"].astype(str) == route_number_str]["route_id"]

    route_trips = trips_df[trips_df["route_id"].isin(route_ids)]

    if "direction_id" in route_trips.columns:
        route_trips = route_trips[route_trips["direction_id"] == direction_id]

    trip_ids = route_trips["trip_id"]
    stop_ids = stop_times_df[stop_times_df["trip_id"].isin(trip_ids)]["stop_id"].unique()
    matched_stops = stops_df[stops_df["stop_id"].isin(stop_ids)]
    return list(zip(matched_stops["stop_lat"], matched_stops["stop_lon"]))


def plotActualStops(routeNumbers):
    all_stops = []
    per_route_stops = {}

    for routeNumber in routeNumbers:
        routeStops = get_stops_for_route(routeNumber, routes, trips, stop_times, stops)
        per_route_stops[routeNumber] = routeStops
        all_stops.extend(routeStops)

    avg_lat = sum(lat for lat, lon in all_stops) / len(all_stops)
    avg_lon = sum(lon for lat, lon in all_stops) / len(all_stops)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

    for i, routeNumber in enumerate(routeNumbers):
        color = COLORS[i % len(COLORS)]

        # Draw the route shape
        routeShapes = getRouteShape(routeNumber, routes, trips, shapes)
        for rNum, coords, shapeColor in routeShapes:
            folium.PolyLine(
                coords,
                color=color,
                weight=5,
                tooltip=f"Route {rNum}"
            ).add_to(m)

        # Draw the actual scheduled stops
        for lat, lon in per_route_stops[routeNumber]:
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=color,
                fill=True,
                fill_color="white",
                fill_opacity=1,
                tooltip=f"Route {routeNumber} stop"
            ).add_to(m)

        print(f"Route {routeNumber}: {len(per_route_stops[routeNumber])} actual stops")

    return m


plotActualStops(ROUTE_NUMBERS).save("actual_bus_stops.html")
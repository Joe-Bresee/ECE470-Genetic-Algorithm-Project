import pandas as pd
import folium

shapes = pd.read_csv("shapes.txt")

routes = pd.read_csv("routes.txt")
trips = pd.read_csv("trips.txt")

route95 = routes[
    routes["route_short_name"] == "95"
]

routeId = route95["route_id"].iloc[0]

print(routeId)

route95_trips = trips[
    trips["route_id"] == routeId
]


shape_id = route95_trips.iloc[0]["shape_id"]

shape = shapes[
    shapes["shape_id"] == shape_id
].sort_values("shape_pt_sequence")

print(shape.head())


center_lat = shape["shape_pt_lat"].mean()
center_lon = shape["shape_pt_lon"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12
)

coords = list(
    zip(
        shape["shape_pt_lat"],
        shape["shape_pt_lon"]
    )
)

folium.PolyLine(
    coords,
    color="blue",
    weight=5
).add_to(m)

m.save("route95.html")
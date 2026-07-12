import pandas as pd
import folium
import math

from busRoutes import getRouteShape 


def segmentLength(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def evenlySpacedPointsOnRoute(coords, numPoints):
    """
    Places `numPoints` points evenly spaced (by distance) along the route.
    Unlike randomStopsOnRoute, this is deterministic - same input always
    gives the same output.
    """

    # Cumulative distance along the route at each vertex
    cumulativeDist = [0]
    for i in range(len(coords) - 1):
        d = segmentLength(coords[i], coords[i + 1])
        cumulativeDist.append(cumulativeDist[-1] + d)

    totalLength = cumulativeDist[-1]

    print(totalLength)

    # Target distances: evenly spaced from 0 to totalLength
    targetDists = [i * totalLength / (numPoints - 1) for i in range(numPoints)]

    points = []
    segIndex = 0

    for target in targetDists:
        # Advance segIndex until target falls within [cumulativeDist[segIndex], cumulativeDist[segIndex+1]]
        while (segIndex < len(cumulativeDist) - 2
               and cumulativeDist[segIndex + 1] < target):
            segIndex += 1

        segStart = cumulativeDist[segIndex]
        segEnd = cumulativeDist[segIndex + 1]
        segLen = segEnd - segStart

        # t = how far along this segment the target distance falls (0 to 1)
        t = 0 if segLen == 0 else (target - segStart) / segLen

        p1 = coords[segIndex]
        p2 = coords[segIndex + 1]
        lat = p1[0] + t * (p2[0] - p1[0])
        lon = p1[1] + t * (p2[1] - p1[1])

        points.append((lat, lon))

    return points


def getPoints():

    print("Generating evenly spaced points along the route...")
    # This needs to not be hardcoded
    ROUTE_NUMBER = 95
    NUMBER_OF_POINTS = 10

    shapes = pd.read_csv("shapes.txt")
    routes = pd.read_csv("routes.txt")
    trips = pd.read_csv("trips.txt")

    routeShapes = getRouteShape(ROUTE_NUMBER, routes, trips, shapes)
    routeNumber, coords, color = routeShapes[0]

    candidateStops = evenlySpacedPointsOnRoute(coords, NUMBER_OF_POINTS)

    totalLength = sum(
        segmentLength(candidateStops[i], candidateStops[i + 1])
        for i in range(len(candidateStops) - 1)
    )
    avgSpacing = totalLength / (len(candidateStops) - 1)
    sigma = avgSpacing * 3

    return candidateStops, sigma

    # Uncomment this if you want to visualize the points on a map
    # -----------------------------------------------------------

    # center_lat = sum(c[0] for c in coords) / len(coords)
    # center_lon = sum(c[1] for c in coords) / len(coords)

    # m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # folium.PolyLine(coords, color=color, weight=5, tooltip=f"Route {routeNumber}").add_to(m)

    # for lat, lon in points:
    #     folium.CircleMarker(
    #         location=[lat, lon],
    #         radius=4,
    #         color=color,
    #         fill=True,
    #         fill_color="white",
    #         fill_opacity=1,
    #     ).add_to(m)

    # m.save("evenlySpacedStops.html")
    # print(f"Saved {len(points)} evenly spaced points to evenlySpacedStops.html")

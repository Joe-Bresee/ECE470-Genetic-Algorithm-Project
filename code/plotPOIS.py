"""
Plots population density (from the equity/census data) as a choropleth,
with nearby POIs overlaid as markers sized by their destination weight.

Reuses (from weight_function.py):
  - _equity_gdf, DAS_NEAR_ROUTE, EQUITY_LOOKUP  (equity/population data)
  - POIS_NEAR_ROUTE, POI_WEIGHT                 (destination data)
  - ROUTE_COORDS                                (for map centering)

Run from the code/ directory (same as ga.py) since data paths are relative.
Importing weight_function triggers its module-level setup (loading GTFS
files, equity geojson, and POI fetch/cache) — same as it does for ga.py.
"""

import folium
import branca.colormap as cm

from weight_function import (
    _equity_gdf,
    DAS_NEAR_ROUTE,
    EQUITY_LOOKUP,
    POIS_NEAR_ROUTE,
    POI_WEIGHT,
    ROUTE_COORDS,
)


def plotPopulationAndPOIs(out_path="population_and_pois.html"):
    avg_lat = sum(lat for lat, lon in ROUTE_COORDS) / len(ROUTE_COORDS)
    avg_lon = sum(lon for lat, lon in ROUTE_COORDS) / len(ROUTE_COORDS)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13, tiles="cartodbpositron")

   
    # --- Population choropleth (DAs near the route) ---
    nearRouteGdf = _equity_gdf[_equity_gdf["DGUID"].isin(DAS_NEAR_ROUTE)]

    colormap = cm.linear.YlOrRd_09.scale(
        nearRouteGdf["population"].min(),
        nearRouteGdf["population"].max(),
    )
    colormap.caption = "Population (dissemination area)"

    folium.GeoJson(
        nearRouteGdf,
        style_function=lambda feature: {
            "fillColor": colormap(feature["properties"]["population"]),
            "color": "gray",
            "weight": 0.5,
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(fields=["population"], aliases=["Population:"]),
    ).add_to(m)

    colormap.add_to(m)     


      # --- Bus route ---
    folium.PolyLine(
        ROUTE_COORDS,
        color="#000000",
        weight=6,
        opacity=1.0,
        tooltip="Route",
    ).add_to(m)


    # --- POI markers, sized by destination weight ---
    for poi in POIS_NEAR_ROUTE:
        weight = POI_WEIGHT.get(poi["type"], 1)
        folium.CircleMarker(
            location=[poi["lat"], poi["lon"]],
            radius=3 + weight * 2,
            color="darkblue",
            fill=True,
            fill_color="darkblue",
            fill_opacity=0.8,
            tooltip=f"{poi['type']} (weight {weight})" + (f" — {poi['name']}" if poi.get("name") else ""),
        ).add_to(m)


   

    m.save(out_path)
    print(f"Saved map to {out_path}")

    return m


if __name__ == "__main__":
    plotPopulationAndPOIs()
# ECE470-Genetic-Algorithm-Project

## Data Download Scripts

The Victoria open data sources used for this project are ArcGIS feature layers, so they can be downloaded directly as GeoJSON with a small script.

Supported out of the box:

- Bike Lanes
- Streets
- Intersections
- Traffic Volume

The ICBC crash dashboards are Tableau Public views, so they are not wired into the same downloader yet and likely need a separate export step.

Usage:

```bash
python scripts/download_arcgis_layer.py --all --output-dir data/raw
```

Or download one layer:

```bash
python scripts/download_arcgis_layer.py --source bike_lanes --output-dir data/raw
```

The script saves both the layer metadata and the combined GeoJSON response for each dataset.

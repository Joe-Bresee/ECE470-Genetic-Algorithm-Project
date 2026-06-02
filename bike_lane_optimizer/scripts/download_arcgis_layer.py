#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


SOURCE_MANIFEST = Path(__file__).with_name("victoria_sources.json")


def load_sources() -> list[dict[str, str]]:
    with SOURCE_MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query_string = urlencode(params or {}, doseq=True)
    request_url = f"{url}?{query_string}" if query_string else url
    with urlopen(request_url) as response:
        return json.load(response)


def layer_metadata(layer_url: str) -> dict[str, Any]:
    return fetch_json(layer_url, {"f": "pjson"})


def query_json(layer_url: str, params: dict[str, Any]) -> dict[str, Any]:
    return fetch_json(f"{layer_url}/query", params)


def chunked(values: list[int], size: int) -> Iterable[list[int]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def download_layer(layer_url: str, output_dir: Path, output_name: str) -> Path:
    metadata = layer_metadata(layer_url)
    object_id_field = metadata.get("objectIdField") or "OBJECTID"
    max_record_count = int(metadata.get("maxRecordCount") or 1000)
    batch_size = min(max_record_count, 1000)

    ids_response = query_json(
        layer_url,
        {
            "where": "1=1",
            "returnIdsOnly": "true",
            "returnDistinctValues": "false",
            "f": "json",
        },
    )
    object_ids = sorted(ids_response.get("objectIds", []))

    features: list[dict[str, Any]] = []
    for batch in chunked(object_ids, batch_size):
        batch_response = query_json(
            layer_url,
            {
                "where": "1=1",
                "objectIds": ",".join(str(object_id) for object_id in batch),
                "outFields": "*",
                "returnGeometry": "true",
                "f": "geojson",
                "outSR": 4326,
            },
        )
        features.extend(batch_response.get("features", []))

    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / f"{output_name}.metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=True)

    geojson_path = output_dir / f"{output_name}.geojson"
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    with geojson_path.open("w", encoding="utf-8") as handle:
        json.dump(geojson, handle)

    print(f"Downloaded {len(features)} records from {metadata.get('name', layer_url)}")
    print(f"Metadata saved to {metadata_path}")
    print(f"GeoJSON saved to {geojson_path}")
    print(f"Object ID field: {object_id_field}")

    return geojson_path


def find_source(sources: list[dict[str, str]], source_name: str) -> dict[str, str]:
    for source in sources:
        if source["name"] == source_name:
            return source
    available = ", ".join(sorted(source["name"] for source in sources))
    raise SystemExit(f"Unknown source '{source_name}'. Available sources: {available}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Victoria ArcGIS feature layers as GeoJSON.")
    parser.add_argument("--source", help="Source name from victoria_sources.json")
    parser.add_argument("--all", action="store_true", help="Download every configured source")
    parser.add_argument("--output-dir", default="data/raw", help="Directory for downloaded files")
    args = parser.parse_args()

    if args.source and args.all:
        raise SystemExit("Use either --source or --all, not both.")

    sources = load_sources()
    output_dir = Path(args.output_dir)

    if args.all or not args.source:
        selected_sources = sources
    else:
        selected_sources = [find_source(sources, args.source)]

    for source in selected_sources:
        download_layer(source["layer_url"], output_dir, source["name"])


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError) as exc:
        raise SystemExit(f"Download failed: {exc}") from exc
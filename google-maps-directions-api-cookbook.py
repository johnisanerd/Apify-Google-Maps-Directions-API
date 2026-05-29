"""
Google Maps Directions API: Thorough Examples Cookbook
See more at: https://apify.com/johnvc/google-maps-directions-api?fpr=9n7kx3
Input schema: https://apify.com/johnvc/google-maps-directions-api/input-schema?fpr=9n7kx3

A catalog of ready-to-run examples covering every input the API supports:
- all travel modes: best, driving, walking, cycling, transit, flight, two-wheeler
- all three ways to set origin/destination: address, coordinates, place ID
- avoidance options (tolls, highways, ferries) and distance units (km/miles)
- localization (country + language)
- transit time (depart at / arrive by) and routing preferences

COST NOTE: each example is one route lookup (a `setup` charge plus one
`directions_processed` charge). To keep your first call cheap, this script runs
ONE example by default. Pass a scenario name to run a specific one, or "all" to
run every example (each one is billed):

    uv run python google-maps-directions-api-cookbook.py            # runs 'basic'
    uv run python google-maps-directions-api-cookbook.py walking
    uv run python google-maps-directions-api-cookbook.py all        # runs all (bills each)

Get your free Apify API key at: https://apify.com?fpr=9n7kx3
"""

import os
import sys

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
ACTOR = "johnvc/google-maps-directions-api"

# ---------------------------------------------------------------------------
# Each scenario is (description, run_input). Together they exercise every input
# the API exposes. Each scenario is a single route, to keep the cost per run low.
# ---------------------------------------------------------------------------
SCENARIOS: dict[str, tuple[str, dict]] = {
    "basic": (
        "Best routes across all modes (the default when travel_mode is omitted)",
        {"start_addr": "New York, NY", "end_addr": "Boston, MA"},
    ),
    "driving": (
        "Driving only, distances reported in miles",
        {"start_addr": "New York, NY", "end_addr": "Boston, MA",
         "travel_mode": "driving", "distance_unit": "miles"},
    ),
    "walking": (
        "Walking directions for a short city route",
        {"start_addr": "Union Square, San Francisco, CA",
         "end_addr": "Ferry Building, San Francisco, CA", "travel_mode": "walking"},
    ),
    "cycling": (
        "Cycling directions",
        {"start_addr": "Union Square, San Francisco, CA",
         "end_addr": "Ferry Building, San Francisco, CA", "travel_mode": "cycling"},
    ),
    "two_wheeler": (
        "Two-wheeler (motorcycle/scooter). Available in select regions, e.g. India",
        {"start_addr": "Connaught Place, New Delhi", "end_addr": "India Gate, New Delhi",
         "travel_mode": "two-wheeler", "gl": "in"},
    ),
    "transit": (
        "Public transit directions",
        {"start_addr": "Brooklyn, NY", "end_addr": "Times Square, New York, NY",
         "travel_mode": "transit"},
    ),
    "transit_advanced": (
        "Transit: arrive by a set time, prefer subway, minimize walking",
        {"start_addr": "Brooklyn, NY", "end_addr": "Times Square, New York, NY",
         "travel_mode": "transit", "transit_prefer": "subway",
         "transit_routing": "less_walking",
         "time_type": "arrive_by", "time_value": "2026-06-01T09:00:00"},
    ),
    "flight": (
        "Flight option for a long-haul route",
        {"start_addr": "New York, NY", "end_addr": "Los Angeles, CA",
         "travel_mode": "flight"},
    ),
    "coordinates": (
        "Origin and destination as latitude,longitude coordinates",
        {"start_coords": "37.7749,-122.4194", "end_coords": "37.3382,-121.8863",
         "travel_mode": "driving"},
    ),
    "place_ids": (
        "Origin and destination as Google Maps place IDs",
        {"start_data_id": "0x89c24fa5d33f083b:0xc80b8f06e177fe62",
         "end_data_id": "0x89e3652d0d3d311b:0x787cbf240162e8a0",
         "travel_mode": "driving"},
    ),
    "avoid": (
        "Driving while avoiding tolls, highways, and ferries",
        {"start_addr": "New York, NY", "end_addr": "Boston, MA", "travel_mode": "driving",
         "avoid_tolls": True, "avoid_highways": True, "avoid_ferries": True},
    ),
    "depart_at": (
        "Driving, leaving at a future time (traffic-aware ETA)",
        {"start_addr": "New York, NY", "end_addr": "Boston, MA", "travel_mode": "driving",
         "time_type": "depart_at", "time_value": "2026-06-01T08:00:00"},
    ),
    "localized": (
        "Localized output: kilometers and French instructions",
        {"start_addr": "Paris, France", "end_addr": "Lyon, France", "travel_mode": "driving",
         "distance_unit": "km", "gl": "fr", "hl": "fr"},
    ),
}


def print_directions(item: dict) -> None:
    """Pretty-print one directions row (or an error/no-route note)."""
    if item.get("result_type") != "directions":
        print("  Note:", item.get("error_message") or item.get("note"))
        return
    print(f"  {item['start']} -> {item['end']}  ({item.get('directions_count', 0)} option(s))")
    if item.get("best_duration"):
        print(f"  Best: {item['best_duration']} / {item.get('best_distance')}")
    for route in item.get("directions", []):
        mode = route.get("travel_mode")
        dur = route.get("formatted_duration") or "n/a"
        dist = route.get("formatted_distance")
        via = route.get("via")
        line = f"    - {mode}: {dur}"
        if dist:
            line += f", {dist}"
        if via:
            line += f" via {via}"
        print(line)
        # Show the first few turn-by-turn steps of the first leg, when present.
        trips = route.get("trips") or []
        if trips:
            for step in (trips[0].get("details") or [])[:3]:
                print(f"        - {step.get('title')} ({step.get('formatted_distance')})")
    durs = item.get("durations") or []
    if durs:
        summary = ", ".join(
            f"{d.get('travel_mode')} {d.get('formatted_duration')}" for d in durs
        )
        print(f"  All modes: {summary}")
    if item.get("google_maps_directions_url"):
        print(f"  Map: {item['google_maps_directions_url']}")


def run_scenario(key: str) -> None:
    description, run_input = SCENARIOS[key]
    print(f"\n=== {key}: {description} ===")
    print(f"Input: {run_input}")
    run = client.actor(ACTOR).call(run_input=run_input)
    # apify-client 3.x returns a typed Run object, so use the attribute.
    items = list(client.dataset(run.default_dataset_id).iterate_items())
    for item in items:
        print_directions(item)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "basic"
    if arg == "all":
        print("Running ALL examples. Each one is a billed route lookup.")
        for key in SCENARIOS:
            run_scenario(key)
    elif arg in SCENARIOS:
        run_scenario(arg)
    else:
        print(f"Unknown example: {arg!r}")
        print("Available examples:", ", ".join(SCENARIOS))
        print('Run one by name, or "all". Example:')
        print("  uv run python google-maps-directions-api-cookbook.py walking")


if __name__ == "__main__":
    main()

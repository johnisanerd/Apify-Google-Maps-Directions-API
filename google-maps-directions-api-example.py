"""
Google Maps Directions API: A Quick Start Example
See more at: https://apify.com/johnvc/google-maps-directions-api?fpr=9n7kx3
Input schema: https://apify.com/johnvc/google-maps-directions-api/input-schema?fpr=9n7kx3

This script shows how to call the Google Maps Directions API on Apify from
Python and read its structured JSON output: route options, distance, ETA, and
turn-by-turn steps between an origin and a destination. It sets several input
parameters so you can see what is configurable, while keeping the run small so
your first call stays cheap.

Get your free Apify API key at: https://apify.com?fpr=9n7kx3
"""

import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize the Apify client with your API token (read from .env)
client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Build the Actor input.
# One route is a single lookup, which keeps this first run inexpensive.
# Raise the scope, or run again for more routes, once you know your budget.
run_input = {
    "start_addr": "New York, NY",
    "end_addr": "Boston, MA",
    "travel_mode": "best",      # best, driving, cycling, walking, transit, flight, two-wheeler
    "distance_unit": "miles",   # auto, km, miles
    "avoid_tolls": False,
    "avoid_highways": False,
    "hl": "en",
    "gl": "us",
}

# Run the Actor and wait for it to finish
run = client.actor("johnvc/google-maps-directions-api").call(run_input=run_input)

# Read structured results from the run's default dataset.
# apify-client 3.x returns a typed Run object, so use the attribute (not run["defaultDatasetId"]).
items = list(client.dataset(run.default_dataset_id).iterate_items())
print(f"Returned {len(items)} item(s).\n")

# Each run returns one row describing the route options for the request.
for item in items:
    if item.get("result_type") != "directions":
        print("Note:", item.get("error_message") or item.get("note"))
        continue

    print(f"{item['start']} -> {item['end']}  ({item.get('directions_count', 0)} option(s))")
    print(f"  Best: {item.get('best_duration')} / {item.get('best_distance')}")
    print(f"  Map:  {item.get('google_maps_directions_url')}\n")

    for route in item.get("directions", []):
        mode = route.get("travel_mode")
        dist = route.get("formatted_distance")
        dur = route.get("formatted_duration")
        via = route.get("via")
        line = f"  - {mode}: {dur}"
        if dist:
            line += f", {dist}"
        if via:
            line += f" via {via}"
        print(line)

        # First few turn-by-turn steps of the first leg, when present
        trips = route.get("trips") or []
        if trips:
            for step in (trips[0].get("details") or [])[:3]:
                print(f"      - {step.get('title')} ({step.get('formatted_distance')})")

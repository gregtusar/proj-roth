#!/usr/bin/env python3
"""Test the location finder capabilities."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.nj_voter_chat_adk.location_finder import LocationFinder, find_location_coords, voters_near_location

print("=" * 60)
print("Testing Location Finder")
print("=" * 60)
print()

# Test location recognition
test_locations = [
    "Summit train station",
    "near Westfield downtown",
    "around Morristown Green",
    "Kean University area",
    "Princeton",
    "Main Street in Summit",
    "123 Broad Street",
    "the mall in Short Hills",
    "overlook hospital",
    "unknown place xyz"
]

print("1. Testing location recognition:")
print("-" * 40)
for location in test_locations:
    coords = LocationFinder.find_coordinates(location)
    if coords:
        print(f"✓ '{location}' -> {coords[0]}, {coords[1]}")
    else:
        print(f"✗ '{location}' -> Not found")
print()

print("2. Testing coordinate query generation:")
print("-" * 40)
test_queries = [
    "Summit train station",
    "downtown Westfield",
    "Main Street",
    "near Elizabeth"
]

for location in test_queries:
    print(f"Location: '{location}'")
    query = LocationFinder.generate_coordinate_query(location)
    print(query[:200] + "..." if len(query) > 200 else query)
    print()

print("3. Testing complete location-based queries:")
print("-" * 40)
query = LocationFinder.create_location_based_query(
    "Summit train station", 
    radius_miles=0.5,
    filters="demo_party = 'DEMOCRAT'"
)
print("Query for Democrats within 0.5 miles of Summit station:")
print(query[:400] + "...")
print()

query = voters_near_location("Westfield downtown", 1.0, "DEMOCRAT")
print("Query using helper function:")
print(query[:300] + "...")
print()

print("4. Testing location suggestions:")
print("-" * 40)
suggestions = LocationFinder.suggest_location_methods("coffee shop in Summit")
print("Suggestions for 'coffee shop in Summit':")
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion[:100]}...")
print()

print("=" * 60)
print("Location Finder Features:")
print("=" * 60)
print("• Recognizes", len(LocationFinder.NJ_LANDMARKS), "NJ landmarks")
print("• Knows coordinates for", len(LocationFinder.NJ_CITY_CENTERS), "NJ cities")
print("• Generates SQL to find coordinates from voter data")
print("• Creates complete radius search queries")
print("• Suggests multiple methods to find coordinates")
print("=" * 60)
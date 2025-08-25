#!/usr/bin/env python3
"""Test the geocoding functionality."""

from .geocoding_tool import GeocodingTool

# Test without API key (will use fallback)
tool = GeocodingTool()

# Test addresses
test_addresses = [
    "Summit, NJ",
    "Westfield train station",
    "123 Main St, Bernardsville, NJ",
    "Morristown Green",
    "Newark Penn Station",
]

print("Testing Geocoding Tool")
print("=" * 50)

for address in test_addresses:
    print(f"\nAddress: {address}")
    result = tool.geocode(address)
    
    if "error" in result:
        print(f"  ❌ Error: {result['error']}")
    else:
        print(f"  ✅ Latitude: {result['latitude']}")
        print(f"     Longitude: {result['longitude']}")
        print(f"     Formatted: {result['formatted_address']}")
        if result.get('approximate'):
            print(f"     Note: {result.get('note', 'Approximate location')}")

print("\n" + "=" * 50)
print("Testing complete!")
print("\nTo enable precise geocoding:")
print("1. Get a Google Maps API key from https://console.cloud.google.com")
print("2. Enable the Geocoding API")
print("3. Set GOOGLE_MAPS_API_KEY environment variable")
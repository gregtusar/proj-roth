#!/usr/bin/env python3
"""Test the lists API directly"""

import requests
import json

# Test without auth first
print("Testing /api/lists without auth:")
response = requests.get("http://localhost:8080/api/lists")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Now test with a fake auth header
print("\nTesting /api/lists with auth header:")
headers = {"Authorization": "Bearer fake-token"}
response = requests.get("http://localhost:8080/api/lists", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Check if it's HTML (React app) or JSON
if response.status_code == 200:
    if response.headers.get('content-type', '').startswith('text/html'):
        print("WARNING: Got HTML response instead of JSON - API route may not be registered")
    else:
        try:
            data = response.json()
            print(f"Parsed JSON: {json.dumps(data, indent=2)[:500]}")
        except:
            print("Could not parse as JSON")
#!/usr/bin/env python3
"""Test the Search Engine ID formats."""

import os
import requests

# The ID from your embed code
search_id = "91907e5365c574113"

print("Testing Search Engine ID formats...")
print("=" * 50)

# Test if you have an API key set
api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
if not api_key:
    print("❌ No API key set. Please set GOOGLE_SEARCH_API_KEY first.")
    print("   You need the API key from Google Cloud Console")
    exit(1)

print(f"✅ Using API Key: {api_key[:10]}...")
print()

# Test different ID formats
test_ids = [
    search_id,  # As provided
    f"{search_id}:omuauf_lfve",  # Common suffix format
    f"017576662512468239146:{search_id}",  # Prefix format (less common)
]

for test_id in test_ids:
    print(f"Testing ID: {test_id}")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": test_id,
        "q": "test",
        "num": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ SUCCESS! This ID works: {test_id}")
            print(f"     Use this as your GOOGLE_SEARCH_ENGINE_ID")
            
            # Set it for testing
            os.environ["GOOGLE_SEARCH_ENGINE_ID"] = test_id
            
            # Do a real search
            data = response.json()
            if "items" in data and data["items"]:
                print(f"     Test search returned: {data['items'][0]['title'][:50]}...")
            break
        elif response.status_code == 400:
            error = response.json().get("error", {}).get("message", "Unknown error")
            if "cx" in error.lower() or "invalid" in error.lower():
                print(f"  ❌ Invalid Search Engine ID")
            else:
                print(f"  ❌ Error: {error[:100]}")
        elif response.status_code == 403:
            print(f"  ❌ API key issue or Custom Search API not enabled")
        else:
            print(f"  ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
    
    print()

print("=" * 50)
print()
print("If none worked, please:")
print("1. Go to https://programmablesearchengine.google.com/controlpanel/all")
print("2. Click on your search engine")
print("3. Look for 'Search engine ID' in the Overview or Setup section")
print("4. It might be labeled as 'cx' parameter")
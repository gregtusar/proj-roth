#!/usr/bin/env python3
"""Quick test of Google Search API configuration."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.nj_voter_chat_adk.google_search_tool import GoogleSearchTool

# Check credentials
api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

print("API Credentials Check:")
print(f"  API Key: {'✅ Set' if api_key else '❌ Not set'}")
print(f"  Engine ID: {'✅ Set' if engine_id else '❌ Not set'}")
print()

if api_key and engine_id:
    print("Testing search...")
    tool = GoogleSearchTool()
    result = tool.search("who is the governor of New Jersey", 1)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Success! Found {result.get('result_count', 0)} results")
        if result.get('results'):
            print(f"   First result: {result['results'][0].get('title', 'N/A')}")
else:
    print("❌ Please set both GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID")
    print("   Run: ./setup_google_search.sh")
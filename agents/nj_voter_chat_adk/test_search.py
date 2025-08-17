#!/usr/bin/env python3
"""Test script for Google Search integration with NJ Voter Chat ADK agent."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_search_tool import GoogleSearchTool


def test_search_tool():
    """Test the Google Search tool directly."""
    print("=" * 60)
    print("Testing Google Search Tool")
    print("=" * 60)
    
    # Create search tool instance
    search_tool = GoogleSearchTool()
    
    # Test queries
    test_queries = [
        "NJ governor election 2025",
        "Bergen County voting locations",
        "New Jersey Democratic primary candidates"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        print("-" * 40)
        
        result = search_tool.search(query, num_results=3)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Total results: {result.get('total_results', 'N/A')}")
            print(f"Search time: {result.get('search_time', 'N/A')}s")
            print(f"Results returned: {result.get('result_count', 0)}")
            
            for i, item in enumerate(result.get('results', []), 1):
                print(f"\n  Result {i}:")
                print(f"    Title: {item.get('title', 'N/A')}")
                print(f"    Link: {item.get('link', 'N/A')}")
                print(f"    Snippet: {item.get('snippet', 'N/A')[:100]}...")
    
    # Test caching
    print("\n" + "=" * 60)
    print("Testing Cache Functionality")
    print("=" * 60)
    
    query = "NJ voter registration deadline"
    print(f"\nFirst call for: {query}")
    result1 = search_tool.search(query, num_results=2)
    print(f"Results: {result1.get('result_count', 0)}")
    
    print(f"\nSecond call for same query (should hit cache):")
    result2 = search_tool.search(query, num_results=2)
    print(f"Results: {result2.get('result_count', 0)}")
    
    # Verify cache hit (results should be identical)
    if result1 == result2:
        print("✓ Cache working correctly - results are identical")
    else:
        print("✗ Cache may not be working - results differ")
    
    # Test rate limiting
    print("\n" + "=" * 60)
    print("Testing Rate Limiting")
    print("=" * 60)
    print("Making rapid requests to test rate limiting...")
    
    for i in range(3):
        result = search_tool.search(f"NJ election test {i}", num_results=1)
        if "error" in result and "rate limit" in result["error"].lower():
            print(f"✓ Rate limiting triggered on request {i+1}")
            break
        else:
            print(f"Request {i+1} completed")


def test_agent_integration():
    """Test the search tool integration with the agent."""
    print("\n" + "=" * 60)
    print("Testing Agent Integration")
    print("=" * 60)
    
    try:
        from agent import google_search
        
        # Test the agent's search function
        query = "current NJ senator"
        print(f"\nTesting agent search function with: {query}")
        result = google_search(query, num_results=2)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"✓ Agent search function working")
            print(f"  Results: {result.get('result_count', 0)}")
            
    except ImportError as e:
        print(f"✗ Could not import agent: {e}")
    except Exception as e:
        print(f"✗ Error testing agent integration: {e}")


if __name__ == "__main__":
    print("Google Search Tool Test Suite")
    print("=" * 60)
    
    # Check if API credentials are configured
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if not api_key or not engine_id:
        print("⚠️  WARNING: Google Search API credentials not configured")
        print("   Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables")
        print("   The tool will still work but return mock/error responses")
        print()
    else:
        print("✓ API credentials configured")
        print()
    
    # Run tests
    test_search_tool()
    test_agent_integration()
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)
#!/usr/bin/env python3
"""
Test the visualization query fix
"""
import asyncio
from backend.services.bigquery_service import execute_query

async def test_queries():
    """Test various query formats to ensure they work"""
    
    test_cases = [
        {
            "name": "Query with full backticks (from Gemini)",
            "query": "SELECT id, name_first FROM `proj-roth.voter_data.voters` LIMIT 5",
            "should_work": True
        },
        {
            "name": "Query without project prefix",
            "query": "SELECT id, name_first FROM voter_data.voters LIMIT 5",
            "should_work": True
        },
        {
            "name": "Query with partial backticks",
            "query": "SELECT id FROM `voter_data.voters` LIMIT 5",
            "should_work": True
        },
        {
            "name": "Complex visualization query",
            "query": """SELECT id, name_first || ' ' || name_last AS name, demo_party AS party, 
                       city, county, ST_X(location) AS longitude, ST_Y(location) AS latitude 
                       FROM `proj-roth.voter_data.voter_geo_view` 
                       WHERE city = 'WESTFIELD' AND demo_party = 'DEMOCRAT' LIMIT 10""",
            "should_work": True
        }
    ]
    
    print("🧪 Testing Visualization Query Fix")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Query: {test['query'][:100]}...")
        
        try:
            result = await execute_query(test['query'])
            
            if result and 'rows' in result:
                print(f"   ✅ SUCCESS: Returned {result['total_rows']} rows")
                print(f"   Executed query: {result['query'][:100]}...")
            else:
                print(f"   ❌ FAILED: No results")
                
        except Exception as e:
            if test['should_work']:
                print(f"   ❌ FAILED: {str(e)[:100]}")
            else:
                print(f"   ✅ Expected failure: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("✨ Testing complete!")

if __name__ == "__main__":
    asyncio.run(test_queries())
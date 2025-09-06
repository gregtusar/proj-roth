#!/usr/bin/env python3
"""
Test the visualization fix directly
"""
import asyncio
from backend.services.bigquery_service import execute_query

async def test_visualization_queries():
    """Test the exact queries that would be generated for visualization"""
    
    print("🧪 Testing Visualization Fix")
    print("=" * 60)
    
    # Test 1: Voters query with correct schema
    print("\n1️⃣ Testing Voters Query (voter_geo_view):")
    voters_query = """
    SELECT 
        master_id, 
        name_first || ' ' || name_last AS name, 
        demo_party AS party, 
        city, 
        county_name AS county, 
        longitude, 
        latitude 
    FROM `proj-roth.voter_data.voter_geo_view` 
    WHERE city = 'WESTFIELD' 
    AND demo_party = 'DEMOCRAT'
    LIMIT 10
    """
    
    try:
        result = await execute_query(voters_query)
        print(f"   ✅ SUCCESS: {result['total_rows']} rows returned")
        if result['rows'] and len(result['rows']) > 0:
            print(f"   Sample: {result['columns']}")
            print(f"   First row: {result['rows'][0][:3]}...")  # Show first 3 fields
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    # Test 2: Streets query
    print("\n2️⃣ Testing Streets Query (street_party_summary):")
    streets_query = """
    SELECT 
        street_name,
        city, 
        county, 
        republican_count, 
        democrat_count, 
        unaffiliated_count, 
        total_voters, 
        republican_pct, 
        democrat_pct, 
        street_center_latitude AS latitude, 
        street_center_longitude AS longitude 
    FROM `proj-roth.voter_data.street_party_summary` 
    WHERE republican_pct > 60 
    AND total_voters >= 10
    LIMIT 10
    """
    
    try:
        result = await execute_query(streets_query)
        print(f"   ✅ SUCCESS: {result['total_rows']} rows returned")
        if result['rows'] and len(result['rows']) > 0:
            print(f"   Sample columns: {result['columns'][:5]}...")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    # Test 3: Simple count to verify basic connectivity
    print("\n3️⃣ Testing Simple Count Query:")
    count_query = "SELECT COUNT(*) as total FROM `proj-roth.voter_data.voters`"
    
    try:
        result = await execute_query(count_query)
        print(f"   ✅ SUCCESS: Total voters = {result['rows'][0][0] if result['rows'] else 'N/A'}")
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("✨ Testing complete!")
    print("\nIf queries are successful, the visualization tool should now work properly.")

if __name__ == "__main__":
    asyncio.run(test_visualization_queries())
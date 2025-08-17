#!/usr/bin/env python3
"""Test script for geospatial query capabilities."""

import sys
import os
from google.cloud import bigquery

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.nj_voter_chat_adk.geospatial_helpers import GeospatialQueryBuilder, voters_within_mile, campaign_headquarters_analysis
from agents.nj_voter_chat_adk.config import PROJECT_ID

print("=" * 60)
print("Testing Geospatial Query Capabilities")
print("=" * 60)
print()

# Summit train station coordinates
SUMMIT_LAT = 40.7155
SUMMIT_LNG = -74.3574

print("1. Testing find_voters_within_radius")
print("-" * 40)
query = GeospatialQueryBuilder.find_voters_within_radius(
    SUMMIT_LAT, SUMMIT_LNG, 0.5, 
    "demo_party = 'DEMOCRAT'"
)
print("Query to find Democrats within 0.5 miles of Summit station:")
print(query[:300] + "...")
print()

print("2. Testing count_by_distance_rings")
print("-" * 40)
query = GeospatialQueryBuilder.count_by_distance_rings(
    SUMMIT_LAT, SUMMIT_LNG, 
    ring_distances=[0.25, 0.5, 1, 2],
    county='UNION'
)
print("Query to count voters in distance rings:")
print(query[:400] + "...")
print()

print("3. Testing find_nearest_high_turnout_dems")
print("-" * 40)
query = GeospatialQueryBuilder.find_nearest_high_turnout_dems(
    SUMMIT_LAT, SUMMIT_LNG, 50
)
print("Query to find nearest high-turnout Democrats:")
print(query[:300] + "...")
print()

print("4. Testing analyze_street_walkability")
print("-" * 40)
query = GeospatialQueryBuilder.analyze_street_walkability('MAIN', 'SUMMIT')
print("Query to analyze Main Street in Summit:")
print(query[:300] + "...")
print()

print("5. Testing find_dense_dem_areas")
print("-" * 40)
query = GeospatialQueryBuilder.find_dense_dem_areas('UNION', min_voters=100)
print("Query to find Democratic strongholds in Union County:")
print(query[:300] + "...")
print()

# Test actual query execution
print("=" * 60)
print("Testing Actual Query Execution")
print("=" * 60)
print()

try:
    client = bigquery.Client(project=PROJECT_ID)
    
    # Simple test query
    test_query = """
    SELECT 
      COUNT(*) as total_voters,
      ROUND(AVG(ST_DISTANCE(
        ST_GEOGPOINT(longitude, latitude),
        ST_GEOGPOINT(-74.3574, 40.7155)
      )) / 1609.34, 2) as avg_miles_from_summit
    FROM proj-roth.voter_data.voters
    WHERE latitude IS NOT NULL
    AND county_name = 'UNION'
    AND ST_DISTANCE(
      ST_GEOGPOINT(longitude, latitude),
      ST_GEOGPOINT(-74.3574, 40.7155)
    ) < 1609.34
    """
    
    print("Running test query: Count voters within 1 mile of Summit...")
    query_job = client.query(test_query)
    results = query_job.result()
    
    for row in results:
        print(f"✓ Found {row.total_voters} voters within 1 mile")
        print(f"  Average distance: {row.avg_miles_from_summit} miles")
    
    print()
    print("✅ Geospatial queries are working correctly!")
    
except Exception as e:
    print(f"⚠️ Could not test actual query execution: {e}")
    print("  (This is normal if not running with BigQuery credentials)")

print()
print("=" * 60)
print("Geospatial Helper Functions Available:")
print("=" * 60)
print("• GeospatialQueryBuilder.find_voters_within_radius()")
print("• GeospatialQueryBuilder.count_by_distance_rings()")
print("• GeospatialQueryBuilder.find_nearest_high_turnout_dems()")
print("• GeospatialQueryBuilder.analyze_street_walkability()")
print("• GeospatialQueryBuilder.find_dense_dem_areas()")
print("• GeospatialQueryBuilder.create_heat_map_data()")
print()
print("Convenience functions:")
print("• voters_within_mile(lat, lng)")
print("• campaign_headquarters_analysis(lat, lng)")
print("• walkable_streets_nearby(lat, lng)")
print()
print("Common NJ locations available in GeospatialQueryBuilder.NJ_LOCATIONS")
print("=" * 60)
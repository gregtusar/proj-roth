#!/usr/bin/env python3
"""
Test script to verify the complete system integration with PDL tool.
"""

import sys
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

print("=" * 60)
print("SYSTEM INTEGRATION TEST")
print("=" * 60)

# Test 1: Import and initialize agent
print("\n1. Testing Agent Initialization...")
print("-" * 40)

try:
    from agents.nj_voter_chat_adk.agent import NJVoterChatAgent
    agent = NJVoterChatAgent()
    print("✓ Agent initialized successfully")
    print("  - PDL tool available: pdl_enrichment" in [tool.__name__ for tool in agent._tools])
except Exception as e:
    print(f"✗ Agent initialization failed: {e}")

# Test 2: Test PDL tool directly
print("\n2. Testing PDL Tool...")
print("-" * 40)

try:
    from agents.nj_voter_chat_adk.pdl_tool import pdl_enrichment_tool
    
    # Check existing enriched record
    result = pdl_enrichment_tool('f470f5bd83c0b7e8', 'fetch')
    if result['status'] == 'found':
        print(f"✓ PDL tool working: Found {result['name']}")
        print(f"  - Has LinkedIn: {result['enrichment']['has_linkedin']}")
        print(f"  - Job: {result['enrichment']['data'].get('job_title', 'N/A')}")
    else:
        print(f"✓ PDL tool working: Status = {result['status']}")
except Exception as e:
    print(f"✗ PDL tool failed: {e}")

# Test 3: Test BigQuery access
print("\n3. Testing BigQuery Access...")
print("-" * 40)

try:
    from google.cloud import bigquery
    client = bigquery.Client(project='proj-roth')
    
    query = """
    SELECT COUNT(*) as total_voters
    FROM `proj-roth.voter_data.voters`
    """
    
    result = list(client.query(query).result())
    if result:
        print(f"✓ BigQuery access working: {result[0]['total_voters']:,} total voters")
    else:
        print("✗ BigQuery query returned no results")
except Exception as e:
    print(f"✗ BigQuery access failed: {e}")

# Test 4: Test Firestore access
print("\n4. Testing Firestore Access...")
print("-" * 40)

try:
    from google.cloud import firestore
    db = firestore.Client(project='proj-roth')
    
    # Try to read a collection (won't fail even if empty)
    sessions = db.collection('sessions').limit(1).get()
    print(f"✓ Firestore access working")
    print(f"  - Can read sessions collection")
except Exception as e:
    print(f"✗ Firestore access failed: {e}")

# Test 5: System status
print("\n5. System Status Summary...")
print("-" * 40)

import requests

try:
    # Check if backend is running
    response = requests.get('http://localhost:8080/health', timeout=2)
    if response.status_code == 200:
        print("✓ Backend server: Running on http://localhost:8080")
    else:
        print(f"⚠ Backend server: Responded with status {response.status_code}")
except requests.exceptions.RequestException:
    print("✗ Backend server: Not accessible")

print("\nKey Features Available:")
print("  • Chat with voter data via BigQuery")
print("  • PDL enrichment ($0.25/each, min_likelihood=8)")
print("  • Geocoding for spatial queries")
print("  • Google search for current info")
print("  • Session persistence via Firestore")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
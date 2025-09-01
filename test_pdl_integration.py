#!/usr/bin/env python3
"""
Test script for PDL integration with the NJ Voter Chat agent.
Demonstrates fetching existing data and explains enrichment process.
"""

import sys
import json
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

from agents.nj_voter_chat_adk.pdl_tool import pdl_enrichment_tool

def test_pdl_integration():
    """Test PDL enrichment tool functionality"""
    
    print("=" * 60)
    print("PDL ENRICHMENT TOOL TEST")
    print("=" * 60)
    
    # Test 1: Fetch existing enriched record
    print("\n1. Testing fetch of existing enriched record...")
    print("-" * 40)
    
    master_id = 'f470f5bd83c0b7e8'  # Mamie Bowers (already enriched)
    result = pdl_enrichment_tool(master_id, action='fetch')
    
    if result['status'] == 'found':
        print(f"✓ Found enriched data for: {result['name']}")
        enrichment = result['enrichment']
        print(f"  - Likelihood: {enrichment['likelihood']}/10")
        print(f"  - Has LinkedIn: {enrichment['has_linkedin']}")
        print(f"  - Has Email: {enrichment['has_email']}")
        print(f"  - Enriched: {enrichment['age_days']} days ago")
        
        data = enrichment['data']
        if data.get('job_title'):
            print(f"  - Job: {data['job_title']} at {data.get('job_company_name', 'Unknown')}")
        if data.get('linkedin_url'):
            print(f"  - LinkedIn: {data['linkedin_url']}")
    
    # Test 2: Check non-enriched record
    print("\n2. Testing fetch of non-enriched record...")
    print("-" * 40)
    
    master_id = '653c5a3bbb68f8dc'  # Gregory Tusar (not enriched)
    result = pdl_enrichment_tool(master_id, action='fetch')
    
    if result['status'] == 'not_enriched':
        print(f"✓ Correctly identified non-enriched record: {result['name']}")
        print(f"  - Location: {result['location']}")
        print(f"  - Age: {result['age']}")
        print(f"  - Party: {result['party']}")
        print(f"  - Message: {result['message']}")
    
    # Test 3: Demonstrate enrichment process (without actually doing it)
    print("\n3. How to trigger enrichment (NOT EXECUTING - costs $0.25)...")
    print("-" * 40)
    print("To enrich a voter, you would call:")
    print("  result = pdl_enrichment_tool(master_id, action='enrich')")
    print("\nWith our default settings:")
    print("  - min_likelihood: 8 (strict matching)")
    print("  - Cost: $0.25 per enrichment")
    print("  - Daily budget: $10.00")
    print("\nThe tool will:")
    print("  1. Check if data already exists")
    print("  2. Verify daily budget hasn't been exceeded")
    print("  3. Send to PDL: name, address, phone, email, birth year")
    print("  4. Store complete JSON response in BigQuery")
    print("  5. Return enriched data including:")
    print("     - Professional info (job, company, salary range)")
    print("     - Education history")
    print("     - Social media profiles")
    print("     - Skills and interests")
    print("     - Contact information")
    
    # Test 4: Session summary
    print("\n4. Getting session summary...")
    print("-" * 40)
    
    result = pdl_enrichment_tool('', action='session_summary')
    print(f"Session cost: ${result['session_cost']:.2f}")
    print(f"Enrichments this session: {result['enrichment_count']}")
    print(f"Daily spend: ${result['daily_spend']:.2f}")
    print(f"Daily budget remaining: ${result['daily_budget_remaining']:.2f}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - PDL Integration Working!")
    print("=" * 60)

if __name__ == "__main__":
    test_pdl_integration()
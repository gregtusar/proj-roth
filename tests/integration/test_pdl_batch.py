#!/usr/bin/env python3
"""
Test script for PDL batch enrichment functionality
"""

import sys
import json
from pathlib import Path

# Add the agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "nj_voter_chat_adk"))

from pdl_tool import PDLEnrichmentTool

def test_batch_enrichment():
    """Test the batch enrichment with sample master_ids"""
    
    # Initialize the tool
    tool = PDLEnrichmentTool()
    
    # Test with a few sample master_ids (replace with actual IDs from your database)
    # You can get these by running: 
    # SELECT master_id FROM proj-roth.voter_data.individuals LIMIT 5
    sample_master_ids = [
        "1000001",  # Replace with actual master_ids
        "1000002",
        "1000003"
    ]
    
    print("Testing PDL Batch Enrichment")
    print("=" * 50)
    
    # Test 1: Check existing enrichments
    print("\n1. Checking existing enrichments for sample IDs...")
    for master_id in sample_master_ids[:2]:
        result = tool.get_enrichment(master_id)
        print(f"  {master_id}: {result.get('status')}")
    
    # Test 2: Batch enrichment (dry run to avoid costs)
    print("\n2. Testing batch enrichment (dry run)...")
    batch_result = tool.trigger_batch_enrichment(
        master_ids=sample_master_ids,
        min_likelihood=8,
        skip_existing=True
    )
    
    print(f"\nBatch Result Status: {batch_result.get('status')}")
    print(f"Batch Result: {json.dumps(batch_result, indent=2, default=str)}")
    
    # Test 3: Session summary
    print("\n3. Getting session summary...")
    summary = tool.get_session_summary()
    print(f"Session Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    try:
        test_batch_enrichment()
        print("\n✅ Batch enrichment test completed successfully")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
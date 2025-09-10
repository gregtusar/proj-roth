#!/usr/bin/env python
"""Test script to verify PDL queries work correctly after JSON-only migration."""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool
import json

def test_pdl_queries():
    tool = BigQueryReadOnlyTool()
    
    test_cases = [
        {
            "name": "Query using pdl_enrichment_view",
            "sql": """
                SELECT 
                    master_id,
                    first_name,
                    last_name,
                    job_title,
                    job_company,
                    job_title_role
                FROM `proj-roth.voter_data.pdl_enrichment_view`
                WHERE job_title IS NOT NULL
                LIMIT 3
            """
        },
        {
            "name": "Direct JSON extraction from pdl_enrichment",
            "sql": """
                SELECT 
                    master_id,
                    JSON_EXTRACT_SCALAR(pdl_data, '$.first_name') as first_name,
                    JSON_EXTRACT_SCALAR(pdl_data, '$.last_name') as last_name,
                    JSON_EXTRACT_SCALAR(pdl_data, '$.job_title') as job_title,
                    JSON_EXTRACT_SCALAR(pdl_data, '$.job_title_role') as job_role
                FROM `proj-roth.voter_data.pdl_enrichment`
                WHERE JSON_EXTRACT_SCALAR(pdl_data, '$.job_title_role') = 'professional_service'
                LIMIT 3
            """
        },
        {
            "name": "Join with individuals table",
            "sql": """
                SELECT 
                    i.name_first,
                    i.name_last,
                    pv.job_title,
                    pv.job_company,
                    pv.likelihood
                FROM `proj-roth.voter_data.individuals` i
                JOIN `proj-roth.voter_data.pdl_enrichment_view` pv
                    ON i.master_id = pv.master_id
                WHERE pv.has_linkedin = TRUE
                    AND pv.likelihood >= 9
                LIMIT 3
            """
        },
        {
            "name": "Complex JSON extraction with filtering",
            "sql": """
                SELECT 
                    COUNT(*) as count,
                    JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_industry') as industry
                FROM `proj-roth.voter_data.pdl_enrichment`
                WHERE pdl_data IS NOT NULL
                    AND JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_industry') IS NOT NULL
                GROUP BY industry
                ORDER BY count DESC
                LIMIT 5
            """
        }
    ]
    
    print("Testing PDL queries after JSON-only migration\n" + "="*50)
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 40)
        
        result = tool.run(test['sql'])
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            print(f"✅ SUCCESS: {result['row_count']} rows returned")
            if result['rows']:
                print("Sample data:")
                for i, row in enumerate(result['rows'][:2]):
                    print(f"  Row {i+1}: {json.dumps(row, indent=2)[:200]}...")
        
        print(f"Execution time: {result.get('elapsed_sec', 'N/A')} seconds")
    
    print("\n" + "="*50)
    print("PDL query testing complete!")

if __name__ == "__main__":
    test_pdl_queries()
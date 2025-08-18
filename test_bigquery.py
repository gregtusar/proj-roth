#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool

# Test the BigQuery tool directly
tool = BigQueryReadOnlyTool()

# Simple test query
test_sql = "SELECT COUNT(*) as total_democrats FROM voter_data.voters WHERE congressional_name = 'NJ-07' AND demo_party = 'DEMOCRAT'"

print(f"Testing query: {test_sql}")
result = tool.run(test_sql)

print(f"\nResult type: {type(result)}")
print(f"Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

if 'error' in result:
    print(f"ERROR: {result['error']}")
else:
    print(f"Row count: {result.get('row_count', 0)}")
    print(f"Rows: {result.get('rows', [])}")
    print(f"Elapsed: {result.get('elapsed_sec', 0)} seconds")

# Try a simpler query
simple_sql = "SELECT COUNT(*) as total FROM voter_data.voters LIMIT 1"
print(f"\n\nTesting simpler query: {simple_sql}")
result2 = tool.run(simple_sql)

if 'error' in result2:
    print(f"ERROR: {result2['error']}")
else:
    print(f"Row count: {result2.get('row_count', 0)}")
    print(f"Rows: {result2.get('rows', [])}")
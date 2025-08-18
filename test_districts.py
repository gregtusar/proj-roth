#\!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool

tool = BigQueryReadOnlyTool()

# Check what congressional districts exist
sql = "SELECT DISTINCT congressional_name FROM voter_data.voters WHERE congressional_name IS NOT NULL ORDER BY congressional_name LIMIT 20"
print(f"Query: {sql}")
result = tool.run(sql)

if 'error' in result:
    print(f"ERROR: {result['error']}")
else:
    print(f"Districts found: {result.get('row_count', 0)}")
    for row in result.get('rows', []):
        print(f"  - {row.get('congressional_name')}")

# Check if it's a different field name
sql2 = "SELECT * FROM voter_data.voters LIMIT 1"
print(f"\n\nChecking first row to see all fields:")
result2 = tool.run(sql2)
if 'rows' in result2 and len(result2['rows']) > 0:
    print("Available fields:")
    for field in result2['rows'][0].keys():
        print(f"  - {field}")

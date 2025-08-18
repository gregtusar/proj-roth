#\!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool

tool = BigQueryReadOnlyTool()

# Test with the mapping
sql = "SELECT COUNT(*) as total_democrats FROM voter_data.voters WHERE congressional_name = 'NJ-07' AND demo_party = 'DEMOCRAT'"
print(f"Query (with mapping): {sql}")
result = tool.run(sql)

if 'error' in result:
    print(f"ERROR: {result['error']}")
else:
    print(f"Democrats found: {result.get('rows', [{}])[0].get('total_democrats', 0):,}")
    print(f"Mapped SQL: {result.get('sql', 'N/A')}")

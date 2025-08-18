#\!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/gregorytusar/proj-roth')

from agents.nj_voter_chat_adk.bigquery_tool import BigQueryReadOnlyTool

tool = BigQueryReadOnlyTool()

# Test with correct district name
sql = "SELECT COUNT(*) as total_democrats FROM voter_data.voters WHERE congressional_name = 'NJ CONGRESSIONAL DISTRICT 07' AND demo_party = 'DEMOCRAT'"
print(f"Query: {sql}")
result = tool.run(sql)

print(f"Democrats in NJ-07: {result.get('rows', [{}])[0].get('total_democrats', 0)}")

# Get breakdown by party
sql2 = """
SELECT 
  demo_party, 
  COUNT(*) as count 
FROM voter_data.voters 
WHERE congressional_name = 'NJ CONGRESSIONAL DISTRICT 07' 
GROUP BY demo_party 
ORDER BY count DESC
"""
print(f"\n\nParty breakdown:")
result2 = tool.run(sql2)
for row in result2.get('rows', []):
    print(f"  {row.get('demo_party', 'Unknown')}: {row.get('count', 0):,}")

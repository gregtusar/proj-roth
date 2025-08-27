#!/usr/bin/env python3
"""
Generate voter_schema.py from BigQuery table schema
This script queries the actual BigQuery table to generate a centralized schema file
"""

import json
from google.cloud import bigquery
from datetime import datetime
import sys
import os

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

project_id = "proj-roth"
dataset_id = "voter_data"
table_id = "voters"

client = bigquery.Client(project=project_id)

def get_table_schema():
    """Get schema information from BigQuery"""
    # First get the table reference to access schema directly
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)
    
    schema_info = []
    for field in table.schema:
        schema_info.append({
            'column_name': field.name,
            'data_type': field.field_type,
            'is_nullable': field.mode != 'REQUIRED',
            'description': field.description or ''
        })
    
    return schema_info

def get_sample_values(column_name, data_type):
    """Get sample values for categorical fields"""
    # Skip fields that are too large or not categorical
    skip_fields = ['voter_record_id', 'vendor_voter_id', 'master_id', 'address_id', 
                   'email', 'phone_1', 'phone_2', 'created_at', 'updated_at']
    
    if column_name in skip_fields or 'participation_' in column_name or 'vote_' in column_name:
        return None
        
    if data_type in ['STRING', 'INT64']:
        try:
            query = f"""
            SELECT DISTINCT {column_name}, COUNT(*) as count
            FROM `{project_id}.{dataset_id}.{table_id}`
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            ORDER BY count DESC
            LIMIT 10
            """
            results = client.query(query)
            values = [row[column_name] for row in results]
            if values:
                return values
        except Exception as e:
            print(f"Could not get sample values for {column_name}: {e}")
    return None

def get_row_count():
    """Get total row count"""
    query = f"""
    SELECT COUNT(*) as total
    FROM `{project_id}.{dataset_id}.{table_id}`
    """
    result = list(client.query(query))[0]
    return result.total

def generate_schema_file():
    """Generate the voter_schema.py file"""
    
    print("Fetching table schema from BigQuery...")
    schema = get_table_schema()
    
    print("Getting row count...")
    row_count = get_row_count()
    
    print("Building field definitions...")
    fields = {}
    
    for field in schema:
        column_name = field['column_name']
        data_type = field['data_type']
        
        field_def = {
            "type": data_type,
            "nullable": field.get('is_nullable', True),
            "description": field.get('description') or f"{column_name} field"
        }
        
        # Get sample values for important fields
        if column_name in ['demo_party', 'county_name', 'municipal_name', 'demo_race', 'demo_gender']:
            print(f"  Getting sample values for {column_name}...")
            values = get_sample_values(column_name, data_type)
            if values:
                field_def["values"] = values
                if values:
                    field_def["example"] = values[0]
        
        # Add examples for specific field types
        if column_name == 'demo_age':
            field_def["example"] = 35
            field_def["range"] = "18-100+"
        elif 'participation_' in column_name:
            field_def["example"] = True
            field_def["description"] = f"Voted in {column_name.replace('participation_', '').replace('_', ' ')}"
        elif column_name == 'voter_record_id':
            field_def["example"] = "703bf4f3-645c-42d6-808f-d354b823b184"
        
        fields[column_name] = field_def
    
    # Create the Python file content
    content = f'''"""
Voter Schema Definition
Auto-generated from BigQuery on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Run scripts/generate_voter_schema.py to regenerate
"""

VOTER_SCHEMA = {{
    "table": "{project_id}.{dataset_id}.{table_id}",
    "row_count": "{row_count:,}",
    "description": "New Jersey Congressional District 07 voter registration data",
    "last_updated": "{datetime.now().isoformat()}",
    
    "fields": {json.dumps(fields, indent=4)},
    
    "query_examples": [
        {{
            "description": "Find Democrats in Union County",
            "natural_language": "Show me all Democrats in Union County",
            "sql": """
                SELECT voter_record_id, demo_party, county_name, demo_age
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE demo_party = 'DEMOCRAT' 
                AND county_name = 'UNION'
                LIMIT 100
            """
        }},
        {{
            "description": "High propensity voters",
            "natural_language": "Find voters who participated in both 2020 and 2022 general elections",
            "sql": """
                SELECT voter_record_id, demo_party, county_name, demo_age
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE participation_general_2020 = true
                AND participation_general_2022 = true
                LIMIT 1000
            """
        }},
        {{
            "description": "Young Republicans",
            "natural_language": "Find Republicans under 30 years old",
            "sql": """
                SELECT voter_record_id, demo_age, demo_party, county_name
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE demo_party = 'REPUBLICAN'
                AND demo_age < 30
                LIMIT 100
            """
        }},
        {{
            "description": "Primary voters by party",
            "natural_language": "Count primary voters by party in 2024",
            "sql": """
                SELECT demo_party, COUNT(*) as voter_count
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE participation_primary_2024 = true
                GROUP BY demo_party
                ORDER BY voter_count DESC
            """
        }},
        {{
            "description": "Unaffiliated voters by county",
            "natural_language": "Find unaffiliated voters grouped by county",
            "sql": """
                SELECT county_name, COUNT(*) as unaffiliated_count
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE demo_party = 'UNAFFILIATED'
                GROUP BY county_name
                ORDER BY unaffiliated_count DESC
            """
        }},
        {{
            "description": "Voter demographics",
            "natural_language": "Show age distribution of active voters",
            "sql": """
                SELECT 
                    CASE 
                        WHEN demo_age BETWEEN 18 AND 29 THEN '18-29'
                        WHEN demo_age BETWEEN 30 AND 44 THEN '30-44'
                        WHEN demo_age BETWEEN 45 AND 64 THEN '45-64'
                        ELSE '65+'
                    END as age_group,
                    COUNT(*) as voter_count
                FROM `{project_id}.{dataset_id}.{table_id}`
                WHERE registration_status = 'ACTIVE'
                GROUP BY age_group
                ORDER BY age_group
            """
        }}
    ],
    
    "common_patterns": {{
        "party_filter": "demo_party = 'DEMOCRAT'",
        "county_filter": "county_name = 'UNION'",
        "age_filter": "demo_age BETWEEN 18 AND 35",
        "high_propensity": "participation_general_2020 = true AND participation_general_2022 = true",
        "primary_voters": "participation_primary_2024 = true",
        "active_voters": "registration_status = 'ACTIVE'",
        "gender_filter": "demo_gender = 'FEMALE'",
        "recent_voters": "participation_general_2024 = true OR participation_primary_2024 = true"
    }},
    
    "important_notes": [
        "All voters are in NJ Congressional District 07",
        "Participation fields are boolean (true/false) indicating if someone voted",
        "Vote fields indicate party ballot pulled in primaries",
        "Counties include: HUNTERDON, SOMERSET, UNION, MORRIS, WARREN, ESSEX, SUSSEX",
        "Party values include: DEMOCRAT, REPUBLICAN, UNAFFILIATED, LIBERTARIAN, GREEN, etc.",
        "Always use LIMIT to avoid querying all 622,000+ records"
    ]
}}

def get_system_prompt(include_examples=True):
    """Generate a system prompt from the schema"""
    prompt = f"""You are a SQL expert for New Jersey voter data analysis.
    
Table: `{{VOTER_SCHEMA['table']}}` ({{VOTER_SCHEMA['row_count']}} records)
{{VOTER_SCHEMA['description']}}

Key fields:
"""
    
    # Add important fields
    important_fields = [
        'voter_record_id', 'demo_party', 'county_name', 'municipal_name',
        'demo_age', 'demo_gender', 'demo_race', 'registration_status',
        'participation_general_2020', 'participation_general_2022', 
        'participation_general_2024', 'participation_primary_2024'
    ]
    
    for field_name in important_fields:
        if field_name in VOTER_SCHEMA['fields']:
            field = VOTER_SCHEMA['fields'][field_name]
            if 'values' in field and field['values']:
                values_str = ', '.join(str(v) for v in field['values'][:3]) + '...'
                prompt += f"- {{field_name}}: {{field['description']}} (values: {{values_str}})\\n"
            else:
                prompt += f"- {{field_name}}: {{field['description']}}\\n"
    
    if include_examples:
        prompt += "\\nExample queries:\\n"
        for example in VOTER_SCHEMA['query_examples'][:3]:
            prompt += f"- {{example['description']}}: {{example['natural_language']}}\\n"
    
    prompt += "\\nImportant notes:\\n"
    for note in VOTER_SCHEMA['important_notes']:
        prompt += f"- {{note}}\\n"
    
    prompt += "\\nGenerate only SELECT queries. Include appropriate WHERE clauses and LIMIT."
    return prompt

def get_query_example(description: str):
    """Get a specific query example by description"""
    for example in VOTER_SCHEMA['query_examples']:
        if description.lower() in example['description'].lower():
            return example
    return None

def get_field_info(field_name: str):
    """Get information about a specific field"""
    if field_name in VOTER_SCHEMA['fields']:
        return VOTER_SCHEMA['fields'][field_name]
    return None

# Cached version of the system prompt for performance
SYSTEM_PROMPT_CACHED = get_system_prompt()
'''
    
    # Write the file
    output_path = "backend/core/voter_schema.py"
    print(f"\nWriting schema to {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Schema file generated successfully!")
    print(f"  Total fields: {len(fields)}")
    print(f"  Total rows: {row_count:,}")
    print(f"  Output: {output_path}")

if __name__ == "__main__":
    generate_schema_file()
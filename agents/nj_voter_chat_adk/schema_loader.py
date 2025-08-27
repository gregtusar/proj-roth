"""
Schema Loader for ADK Agent
Loads the centralized voter schema for use in the ADK agent
"""

import sys
import os

# Add backend directory to path to import voter_schema
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from core.voter_schema import (
        VOTER_SCHEMA, 
        get_system_prompt, 
        get_query_example,
        get_field_info,
        SYSTEM_PROMPT_CACHED
    )
    
    def get_schema_context():
        """Get schema context for the ADK agent"""
        context = f"""
Database Schema Information:
Table: {VOTER_SCHEMA['table']} ({VOTER_SCHEMA['row_count']} records)
{VOTER_SCHEMA['description']}

Key Fields with Sample Values:
"""
        # Add field information
        important_fields = [
            'voter_record_id', 'demo_party', 'county_name', 'municipal_name',
            'demo_age', 'demo_gender', 'demo_race', 'registration_status'
        ]
        
        for field_name in important_fields:
            if field_name in VOTER_SCHEMA['fields']:
                field = VOTER_SCHEMA['fields'][field_name]
                if 'values' in field and field['values']:
                    values_str = ', '.join(str(v) for v in field['values'][:5])
                    context += f"- {field_name}: {values_str}\n"
                elif 'example' in field:
                    context += f"- {field_name}: example = {field['example']}\n"
                else:
                    context += f"- {field_name}: {field['type']}\n"
        
        context += "\nQuery Examples:\n"
        for example in VOTER_SCHEMA['query_examples']:
            context += f"\n{example['description']}:\n"
            context += f"SQL: {example['sql'].strip()}\n"
        
        return context
    
    # Export for use in config.py
    SCHEMA_CONTEXT = get_schema_context()
    
except ImportError as e:
    print(f"Warning: Could not load voter_schema: {e}")
    print("Run scripts/generate_voter_schema.py to generate the schema file")
    
    # Provide a fallback
    VOTER_SCHEMA = {
        "table": "proj-roth.voter_data.voters",
        "row_count": "622,000+",
        "fields": {},
        "query_examples": [],
        "common_patterns": {}
    }
    SCHEMA_CONTEXT = "Schema information not available. Please run scripts/generate_voter_schema.py"
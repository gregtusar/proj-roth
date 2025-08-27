"""
Voter Schema Definition
Auto-generated from BigQuery on 2025-08-27 13:19:43
Run scripts/generate_voter_schema.py to regenerate
"""

VOTER_SCHEMA = {
    "table": "proj-roth.voter_data.voters",
    "row_count": "623,536",
    "description": "New Jersey Congressional District 07 voter registration data",
    "last_updated": "2025-08-27T13:19:43.356778",
    
    "fields": {
    "voter_record_id": {
        "type": "STRING",
        "nullable": True,
        "description": "voter_record_id field",
        "example": "703bf4f3-645c-42d6-808f-d354b823b184"
    },
    "vendor_voter_id": {
        "type": "STRING",
        "nullable": True,
        "description": "vendor_voter_id field"
    },
    "master_id": {
        "type": "STRING",
        "nullable": True,
        "description": "master_id field"
    },
    "address_id": {
        "type": "STRING",
        "nullable": True,
        "description": "address_id field"
    },
    "demo_party": {
        "type": "STRING",
        "nullable": True,
        "description": "demo_party field",
        "values": [
            "REPUBLICAN",
            "UNAFFILIATED",
            "DEMOCRAT",
            "LIBERTARIAN",
            "CONSERVATIVE",
            "GREEN",
            "CONSTITUTION",
            "SOCIALIST",
            "NATURAL LAW",
            "REFORM"
        ],
        "example": "REPUBLICAN"
    },
    "demo_age": {
        "type": "INTEGER",
        "nullable": True,
        "description": "demo_age field",
        "example": 35,
        "range": "18-100+"
    },
    "demo_race": {
        "type": "STRING",
        "nullable": True,
        "description": "demo_race field",
        "values": [
            "WHITE",
            "LATINO/A",
            "ASIAN",
            "BLACK",
            "OTHER",
            "NATIVE AMERICAN"
        ],
        "example": "WHITE"
    },
    "demo_race_confidence": {
        "type": "STRING",
        "nullable": True,
        "description": "demo_race_confidence field"
    },
    "demo_gender": {
        "type": "STRING",
        "nullable": True,
        "description": "demo_gender field",
        "values": [
            "FEMALE",
            "MALE",
            "UNKNOWN"
        ],
        "example": "FEMALE"
    },
    "registration_status": {
        "type": "STRING",
        "nullable": True,
        "description": "registration_status field"
    },
    "voter_type": {
        "type": "STRING",
        "nullable": True,
        "description": "voter_type field"
    },
    "congressional_district": {
        "type": "STRING",
        "nullable": True,
        "description": "congressional_district field"
    },
    "state_house_district": {
        "type": "STRING",
        "nullable": True,
        "description": "state_house_district field"
    },
    "state_senate_district": {
        "type": "STRING",
        "nullable": True,
        "description": "state_senate_district field"
    },
    "precinct": {
        "type": "STRING",
        "nullable": True,
        "description": "precinct field"
    },
    "municipal_name": {
        "type": "STRING",
        "nullable": True,
        "description": "municipal_name field"
    },
    "county_name": {
        "type": "STRING",
        "nullable": True,
        "description": "county_name field",
        "values": [
            "UNION",
            "SOMERSET",
            "HUNTERDON",
            "MORRIS",
            "WARREN",
            "SUSSEX"
        ],
        "example": "UNION"
    },
    "city_council_district": {
        "type": "STRING",
        "nullable": True,
        "description": "city_council_district field"
    },
    "score_support_generic_dem": {
        "type": "FLOAT",
        "nullable": True,
        "description": "score_support_generic_dem field"
    },
    "current_support_score": {
        "type": "FLOAT",
        "nullable": True,
        "description": "current_support_score field"
    },
    "participation_primary_2016": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2016",
        "example": True
    },
    "participation_primary_2017": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2017",
        "example": True
    },
    "participation_primary_2018": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2018",
        "example": True
    },
    "participation_primary_2019": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2019",
        "example": True
    },
    "participation_primary_2020": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2020",
        "example": True
    },
    "participation_primary_2021": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2021",
        "example": True
    },
    "participation_primary_2022": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2022",
        "example": True
    },
    "participation_primary_2023": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2023",
        "example": True
    },
    "participation_primary_2024": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in primary 2024",
        "example": True
    },
    "participation_general_2016": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2016",
        "example": True
    },
    "participation_general_2017": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2017",
        "example": True
    },
    "participation_general_2018": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2018",
        "example": True
    },
    "participation_general_2019": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2019",
        "example": True
    },
    "participation_general_2020": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2020",
        "example": True
    },
    "participation_general_2021": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2021",
        "example": True
    },
    "participation_general_2022": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2022",
        "example": True
    },
    "participation_general_2023": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2023",
        "example": True
    },
    "participation_general_2024": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "Voted in general 2024",
        "example": True
    },
    "vote_primary_dem_2016": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2016 field"
    },
    "vote_primary_rep_2016": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2016 field"
    },
    "vote_primary_dem_2017": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2017 field"
    },
    "vote_primary_rep_2017": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2017 field"
    },
    "vote_primary_dem_2018": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2018 field"
    },
    "vote_primary_rep_2018": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2018 field"
    },
    "vote_primary_dem_2019": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2019 field"
    },
    "vote_primary_rep_2019": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2019 field"
    },
    "vote_primary_dem_2020": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2020 field"
    },
    "vote_primary_rep_2020": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2020 field"
    },
    "vote_primary_dem_2021": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2021 field"
    },
    "vote_primary_rep_2021": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2021 field"
    },
    "vote_primary_dem_2022": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2022 field"
    },
    "vote_primary_rep_2022": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2022 field"
    },
    "vote_primary_dem_2023": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2023 field"
    },
    "vote_primary_rep_2023": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2023 field"
    },
    "vote_primary_dem_2024": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_dem_2024 field"
    },
    "vote_primary_rep_2024": {
        "type": "BOOLEAN",
        "nullable": True,
        "description": "vote_primary_rep_2024 field"
    },
    "email": {
        "type": "STRING",
        "nullable": True,
        "description": "email field"
    },
    "phone_1": {
        "type": "STRING",
        "nullable": True,
        "description": "phone_1 field"
    },
    "phone_2": {
        "type": "STRING",
        "nullable": True,
        "description": "phone_2 field"
    },
    "created_at": {
        "type": "TIMESTAMP",
        "nullable": True,
        "description": "created_at field"
    },
    "updated_at": {
        "type": "TIMESTAMP",
        "nullable": True,
        "description": "updated_at field"
    },
    "rn": {
        "type": "INTEGER",
        "nullable": True,
        "description": "rn field"
    }
},
    
    "query_examples": [
        {
            "description": "Find Democrats in Union County",
            "natural_language": "Show me all Democrats in Union County",
            "sql": """
                SELECT voter_record_id, demo_party, county_name, demo_age
                FROM `proj-roth.voter_data.voters`
                WHERE demo_party = 'DEMOCRAT' 
                AND county_name = 'UNION'
                LIMIT 100
            """
        },
        {
            "description": "High propensity voters",
            "natural_language": "Find voters who participated in both 2020 and 2022 general elections",
            "sql": """
                SELECT voter_record_id, demo_party, county_name, demo_age
                FROM `proj-roth.voter_data.voters`
                WHERE participation_general_2020 = true
                AND participation_general_2022 = true
                LIMIT 1000
            """
        },
        {
            "description": "Young Republicans",
            "natural_language": "Find Republicans under 30 years old",
            "sql": """
                SELECT voter_record_id, demo_age, demo_party, county_name
                FROM `proj-roth.voter_data.voters`
                WHERE demo_party = 'REPUBLICAN'
                AND demo_age < 30
                LIMIT 100
            """
        },
        {
            "description": "Primary voters by party",
            "natural_language": "Count primary voters by party in 2024",
            "sql": """
                SELECT demo_party, COUNT(*) as voter_count
                FROM `proj-roth.voter_data.voters`
                WHERE participation_primary_2024 = true
                GROUP BY demo_party
                ORDER BY voter_count DESC
            """
        },
        {
            "description": "Unaffiliated voters by county",
            "natural_language": "Find unaffiliated voters grouped by county",
            "sql": """
                SELECT county_name, COUNT(*) as unaffiliated_count
                FROM `proj-roth.voter_data.voters`
                WHERE demo_party = 'UNAFFILIATED'
                GROUP BY county_name
                ORDER BY unaffiliated_count DESC
            """
        },
        {
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
                FROM `proj-roth.voter_data.voters`
                WHERE registration_status = 'ACTIVE'
                GROUP BY age_group
                ORDER BY age_group
            """
        }
    ],
    
    "common_patterns": {
        "party_filter": "demo_party = 'DEMOCRAT'",
        "county_filter": "county_name = 'UNION'",
        "age_filter": "demo_age BETWEEN 18 AND 35",
        "high_propensity": "participation_general_2020 = true AND participation_general_2022 = true",
        "primary_voters": "participation_primary_2024 = true",
        "active_voters": "registration_status = 'ACTIVE'",
        "gender_filter": "demo_gender = 'FEMALE'",
        "recent_voters": "participation_general_2024 = true OR participation_primary_2024 = true"
    },
    
    "important_notes": [
        "All voters are in NJ Congressional District 07",
        "Participation fields are boolean (true/false) indicating if someone voted",
        "Vote fields indicate party ballot pulled in primaries",
        "Counties include: HUNTERDON, SOMERSET, UNION, MORRIS, WARREN, ESSEX, SUSSEX",
        "Party values include: DEMOCRAT, REPUBLICAN, UNAFFILIATED, LIBERTARIAN, GREEN, etc.",
        "Always use LIMIT to avoid querying all 622,000+ records"
    ]
}

def get_system_prompt(include_examples=True):
    """Generate a system prompt from the schema"""
    prompt = f"""You are a SQL expert for New Jersey voter data analysis.
    
Table: `{VOTER_SCHEMA['table']}` ({VOTER_SCHEMA['row_count']} records)
{VOTER_SCHEMA['description']}

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
                prompt += f"- {field_name}: {field['description']} (values: {values_str})\n"
            else:
                prompt += f"- {field_name}: {field['description']}\n"
    
    if include_examples:
        prompt += "\nExample queries:\n"
        for example in VOTER_SCHEMA['query_examples'][:3]:
            prompt += f"- {example['description']}: {example['natural_language']}\n"
    
    prompt += "\nImportant notes:\n"
    for note in VOTER_SCHEMA['important_notes']:
        prompt += f"- {note}\n"
    
    prompt += "\nGenerate only SELECT queries. Include appropriate WHERE clauses and LIMIT."
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

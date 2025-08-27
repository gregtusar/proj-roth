"""
Database Manifest for NJ Voter Data Analysis Framework
This manifest provides comprehensive documentation of all tables, views, and their relationships.
Used by both the ADK agent and the Query Tool for SQL generation guidance.
"""

DATABASE_MANIFEST = {
    "overview": """
    The NJ Voter Data Analysis Framework contains normalized data for 622,000+ voters in 
    Congressional District 07, including voter registration, voting history, campaign donations, 
    and geocoded addresses. Data is organized in a star schema with master_id and address_id 
    serving as primary keys for linking records across tables.
    
    KEY PRINCIPLES:
    - Use specific values when querying (e.g., demo_party = 'REPUBLICAN' not 'Republican')  
    - Join tables using master_id to link individuals across datasets
    - Join using address_id to get geocoded location data
    - Use BigQuery geography functions for spatial analysis (ST_DISTANCE, ST_DWITHIN, etc.)
    - Avoid using LIMIT unless specifically requested by the user
    """,
    
    "tables": {
        "voters": {
            "description": "Core voter registration table with 622K+ records from NJ District 07",
            "primary_key": "voter_record_id",
            "foreign_keys": ["master_id", "address_id"],
            "key_fields": {
                "voter_record_id": "Unique identifier for each voter record",
                "vendor_voter_id": "Original ID from data vendor",
                "master_id": "Links to individuals table for normalized person data",
                "address_id": "Links to addresses table for geocoded location",
                "demo_party": "Party affiliation: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED' (exact case)",
                "demo_age": "Voter age",
                "demo_race": "Racial/ethnic identity", 
                "demo_gender": "Gender identity",
                "county_name": "County of residence",
                "congressional_district": "Congressional district (stored as 'NJ CONGRESSIONAL DISTRICT 07')",
                "participation_general_YYYY": "Boolean - voted in general election for year YYYY",
                "participation_primary_YYYY": "Boolean - voted in primary election for year YYYY",
                "vote_primary_dem_YYYY": "Boolean - voted in Democratic primary for year YYYY",
                "vote_primary_rep_YYYY": "Boolean - voted in Republican primary for year YYYY"
            },
            "hints": [
                "To find voters by party, use exact values: demo_party = 'REPUBLICAN'",
                "Voting history fields span 2016-2024 for both primary and general elections",
                "Use participation fields to identify voting frequency patterns",
                "Congressional district stored as full name, not abbreviation"
            ]
        },
        
        "individuals": {
            "description": "Normalized person records deduplicated across all data sources",
            "primary_key": "master_id",
            "key_fields": {
                "master_id": "Unique person identifier used across all tables",
                "standardized_name": "Full name in standardized format",
                "name_first": "First name",
                "name_middle": "Middle name/initial",
                "name_last": "Last name",
                "name_suffix": "Name suffix (Jr., Sr., III, etc.)"
            },
            "hints": [
                "This table contains deduplicated individuals",
                "Use master_id to join with voters, donations, and individual_addresses",
                "standardized_name useful for fuzzy matching and display"
            ]
        },
        
        "addresses": {
            "description": "264K unique geocoded addresses with latitude/longitude",
            "primary_key": "address_id",
            "key_fields": {
                "address_id": "Unique address identifier",
                "standardized_address": "Full address in standardized format",
                "street_number": "House/building number",
                "street_name": "Street name without suffix",
                "street_suffix": "Street type (St, Ave, Rd, etc.)",
                "city": "City name",
                "state": "State abbreviation (NJ)",
                "zip_code": "5-digit ZIP code",
                "county": "County name",
                "latitude": "Geocoded latitude",
                "longitude": "Geocoded longitude",
                "geo_location": "BigQuery GEOGRAPHY type for spatial queries"
            },
            "hints": [
                "All 264K addresses have been geocoded with preserved lat/lng",
                "Use geo_location field with ST_* functions for spatial analysis",
                "Join with voters or donations using address_id"
            ]
        },
        
        "donations": {
            "description": "Campaign contribution records matched to voter records",
            "primary_key": "donation_record_id",
            "foreign_keys": ["master_id", "address_id"],
            "key_fields": {
                "donation_record_id": "Unique donation identifier",
                "master_id": "Links to individuals table (may be NULL if unmatched)",
                "address_id": "Links to addresses table (may be NULL if unmatched)",
                "committee_name": "Recipient committee/campaign name",
                "contribution_amount": "Donation amount in dollars",
                "election_type": "Type of election (Primary, General, etc.)",
                "election_year": "Year of the election",
                "employer": "Donor's employer",
                "occupation": "Donor's occupation",
                "donation_date": "Date of contribution",
                "original_full_name": "Original name from donation record",
                "original_address": "Original address from donation record",
                "match_confidence": "Confidence score for voter match (0-1)",
                "match_method": "Method used for matching (exact, fuzzy, etc.)"
            },
            "hints": [
                "~24% of donations matched to voter records using fuzzy matching",
                "Join with individuals using master_id to get donor details",
                "Join with addresses using address_id for donor location",
                "Use match_confidence to filter for high-quality matches",
                "Original fields preserved for unmatched records"
            ]
        },
        
        "individual_addresses": {
            "description": "Links individuals to their addresses (many-to-many relationship)",
            "foreign_keys": ["master_id", "address_id"],
            "key_fields": {
                "master_id": "Individual identifier",
                "address_id": "Address identifier",
                "address_type": "Type of address (residential, mailing, etc.)",
                "is_primary": "Boolean - primary address for this individual"
            },
            "hints": [
                "Use this to find all addresses associated with an individual",
                "Join with addresses table to get full address details"
            ]
        },
        
        "street_party_summary": {
            "description": "Pre-aggregated party statistics by street for quick analysis",
            "key_fields": {
                "street_name": "Street name",
                "city": "City name",
                "county": "County name",
                "zip_code": "ZIP code",
                "republican_count": "Number of Republican voters",
                "democrat_count": "Number of Democrat voters",
                "unaffiliated_count": "Number of unaffiliated voters",
                "total_voters": "Total voters on street",
                "republican_pct": "Percentage Republican",
                "democrat_pct": "Percentage Democrat",
                "street_center_location": "Geographic center of street",
                "street_center_latitude": "Center latitude",
                "street_center_longitude": "Center longitude"
            },
            "hints": [
                "Pre-calculated for streets with 3+ voters (privacy protection)",
                "Use for quick party composition analysis by geography",
                "Includes geographic center for mapping"
            ]
        }
    },
    
    "views": {
        "voter_geo_view": {
            "description": "Complete voter information with joined individual and address data",
            "base_tables": ["voters", "individuals", "addresses"],
            "hints": [
                "USE THIS VIEW for most voter queries - it has everything joined",
                "Includes full voter info, names, addresses, and geocoding",
                "No need to write complex joins - this view does it for you"
            ]
        },
        
        "donor_view": {
            "description": "Donation records enriched with donor and address information",
            "base_tables": ["donations", "individuals", "addresses", "voters"],
            "key_fields": {
                "is_registered_voter": "Boolean - donor is also a registered voter",
                "voter_party": "Party affiliation if donor is registered voter",
                "voter_county": "County if donor is registered voter"
            },
            "hints": [
                "USE THIS VIEW to analyze campaign contributions",
                "Shows which donors are also registered voters",
                "Includes geocoding for matched addresses"
            ]
        },
        
        "high_frequency_voters": {
            "description": "Voters who participated in 75%+ of elections since 2016",
            "hints": [
                "Pre-filtered view of consistent voters",
                "Useful for targeting likely voters"
            ]
        },
        
        "major_donors": {
            "description": "Individuals with significant campaign contributions",
            "hints": [
                "Aggregated donation amounts by individual",
                "Includes total contributions and committee counts"
            ]
        },
        
        "voter_donor_mv": {
            "description": "Materialized view linking voters to their donation history",
            "hints": [
                "Pre-computed for performance",
                "Use for quick voter-donor analysis"
            ]
        },
        
        "voter_geo_summary_mv": {
            "description": "Materialized geographic summary statistics",
            "hints": [
                "Pre-aggregated voter counts by geography",
                "Optimized for geographic analysis queries"
            ]
        }
    },
    
    "relationships": {
        "master_id": {
            "description": "Primary person identifier linking across tables",
            "joins": [
                "voters.master_id = individuals.master_id",
                "donations.master_id = individuals.master_id",
                "individual_addresses.master_id = individuals.master_id"
            ]
        },
        "address_id": {
            "description": "Primary address identifier for location data",
            "joins": [
                "voters.address_id = addresses.address_id",
                "donations.address_id = addresses.address_id",
                "individual_addresses.address_id = addresses.address_id"
            ]
        }
    },
    
    "query_patterns": {
        "find_voters_by_location": {
            "description": "Find voters within a certain distance of a point",
            "example": """
                SELECT * FROM voter_geo_view
                WHERE ST_DWITHIN(geo_location, ST_GEOGPOINT(longitude, latitude), distance_meters)
            """,
            "notes": "Use ST_DWITHIN for efficient spatial queries"
        },
        
        "match_donors_to_voters": {
            "description": "Find donors who are registered voters",
            "example": """
                SELECT * FROM donor_view 
                WHERE is_registered_voter = TRUE
            """,
            "notes": "donor_view already has the joins done"
        },
        
        "analyze_street_politics": {
            "description": "Get party composition by street",
            "example": """
                SELECT * FROM street_party_summary
                WHERE city = 'SUMMIT' AND total_voters >= 10
                ORDER BY republican_pct DESC
            """,
            "notes": "Pre-aggregated for performance"
        },
        
        "voting_frequency_analysis": {
            "description": "Find voters by participation patterns",
            "example": """
                SELECT * FROM voters
                WHERE participation_general_2020 = TRUE 
                  AND participation_general_2022 = TRUE
                  AND participation_general_2024 = TRUE
            """,
            "notes": "Use participation fields for turnout analysis"
        },
        
        "geographic_clustering": {
            "description": "Find geographic centers of voter groups",
            "example": """
                SELECT demo_party,
                       ST_CENTROID(ST_UNION_AGG(geo_location)) as center,
                       COUNT(*) as voter_count
                FROM voter_geo_view
                WHERE county = 'UNION'
                GROUP BY demo_party
            """,
            "notes": "ST_CENTROID finds geographic center of group"
        }
    },
    
    "important_notes": [
        "Party values must be exact: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED' (case-sensitive)",
        "Congressional district stored as 'NJ CONGRESSIONAL DISTRICT 07' not 'NJ-07'",
        "All 264K addresses have preserved geocoding (latitude/longitude)",
        "Use voter_geo_view for most queries - it has everything pre-joined",
        "Use donor_view for donation analysis - includes voter matching",
        "Fuzzy matching on donations ignores ZIP codes due to data corruption",
        "Do NOT use LIMIT unless the user specifically requests it",
        "Use ST_* geography functions for all spatial analysis",
        "master_id and address_id are the primary keys for joining",
        "Voting history available for years 2016-2024"
    ]
}

def get_table_info(table_name: str) -> dict:
    """Get information about a specific table or view."""
    if table_name in DATABASE_MANIFEST["tables"]:
        return DATABASE_MANIFEST["tables"][table_name]
    elif table_name in DATABASE_MANIFEST["views"]:
        return DATABASE_MANIFEST["views"][table_name]
    return None

def get_join_hints(table1: str, table2: str) -> list:
    """Get hints for joining two tables."""
    hints = []
    
    # Check for direct relationships via master_id
    if "master_id" in str(DATABASE_MANIFEST["tables"].get(table1, {})) and \
       "master_id" in str(DATABASE_MANIFEST["tables"].get(table2, {})):
        hints.append(f"Join {table1} and {table2} on master_id")
    
    # Check for direct relationships via address_id  
    if "address_id" in str(DATABASE_MANIFEST["tables"].get(table1, {})) and \
       "address_id" in str(DATABASE_MANIFEST["tables"].get(table2, {})):
        hints.append(f"Join {table1} and {table2} on address_id")
    
    return hints

def get_query_guidance() -> str:
    """Get general guidance for writing queries."""
    return f"""
    {DATABASE_MANIFEST['overview']}
    
    Key Rules:
    {chr(10).join('- ' + note for note in DATABASE_MANIFEST['important_notes'])}
    
    Recommended Views:
    - voter_geo_view: Use for most voter queries (pre-joined with names and addresses)
    - donor_view: Use for donation analysis (includes voter matching)
    
    Common Patterns:
    {chr(10).join(f"- {k}: {v['description']}" for k, v in DATABASE_MANIFEST['query_patterns'].items())}
    """

def get_available_tables() -> list:
    """Get list of all available tables and views."""
    tables = list(DATABASE_MANIFEST["tables"].keys())
    views = list(DATABASE_MANIFEST["views"].keys())
    return tables + views

def format_for_llm() -> str:
    """Format the manifest for LLM consumption."""
    output = []
    output.append("DATABASE SCHEMA AND QUERY GUIDANCE")
    output.append("=" * 40)
    output.append(DATABASE_MANIFEST["overview"])
    output.append("")
    
    output.append("TABLES:")
    for table_name, info in DATABASE_MANIFEST["tables"].items():
        output.append(f"\n{table_name}: {info['description']}")
        if "key_fields" in info:
            for field, desc in list(info["key_fields"].items())[:5]:  # Show top 5 fields
                output.append(f"  - {field}: {desc}")
        if "hints" in info:
            output.append(f"  Hints: {'; '.join(info['hints'][:2])}")
    
    output.append("\nVIEWS (Recommended for queries):")
    for view_name, info in DATABASE_MANIFEST["views"].items():
        output.append(f"\n{view_name}: {info['description']}")
        if "hints" in info:
            output.append(f"  Hints: {'; '.join(info['hints'][:2])}")
    
    output.append("\nIMPORTANT RULES:")
    for note in DATABASE_MANIFEST["important_notes"][:7]:  # Show top 7 rules
        output.append(f"- {note}")
    
    return "\n".join(output)
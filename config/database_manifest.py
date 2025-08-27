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
    - Names are stored as 'LASTNAME, FIRSTNAME' format in standardized fields
    - Always use 'city' field NOT 'municipal_name' (which is often NULL)
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
                "demo_party": "Party affiliation: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED', 'LIBERTARIAN', 'CONSERVATIVE', 'CONSTITUTION', 'GREEN' (exact case)",
                "demo_age": "Voter age",
                "demo_race": "Race AND ethnicity field (e.g., contains 'Latino', 'Hispanic', 'Asian', 'Black', 'White', etc.)", 
                "demo_gender": "Gender identity ('M', 'F', or NULL)",
                "county_name": "County of residence (UPPERCASE like 'UNION', 'MORRIS')",
                "congressional_district": "Congressional district (stored as 'NJ CONGRESSIONAL DISTRICT 07')",
                "state_house_district": "State Assembly district",
                "state_senate_district": "State Senate district", 
                "precinct": "Voting precinct",
                "participation_general_YYYY": "Boolean - voted in general election for year YYYY",
                "participation_primary_YYYY": "Boolean - voted in primary election for year YYYY",
                "vote_primary_dem_YYYY": "Boolean - voted in Democratic primary for year YYYY",
                "vote_primary_rep_YYYY": "Boolean - voted in Republican primary for year YYYY",
                "registration_status": "Active/Inactive status",
                "voter_type": "Type of voter",
                "score_support_generic_dem": "Generic Democratic support score (0-1)",
                "current_support_score": "Current support score (0-1)"
            },
            "hints": [
                "To find voters by party, use exact values: demo_party = 'REPUBLICAN'",
                "IMPORTANT: demo_race contains BOTH race AND ethnicity (Latino/Hispanic are in this field)",
                "Voting history fields span 2016-2024 for both primary and general elections",
                "Use participation fields to identify voting frequency patterns",
                "Congressional district stored as full name, not abbreviation",
                "Names in original voters table are CASE SENSITIVE"
            ]
        },
        
        "individuals": {
            "description": "Normalized person records deduplicated across all data sources (619K unique people)",
            "primary_key": "master_id",
            "key_fields": {
                "master_id": "Unique person identifier used across all tables",
                "standardized_name": "Full name in 'LASTNAME, FIRSTNAME' format",
                "name_first": "First name",
                "name_middle": "Middle name/initial",
                "name_last": "Last name",
                "name_suffix": "Name suffix (Jr., Sr., III, etc.)"
            },
            "hints": [
                "This table contains deduplicated individuals",
                "Use master_id to join with voters, donations, and individual_addresses",
                "standardized_name format is 'LASTNAME, FIRSTNAME' (e.g., 'SMITH, JOHN')",
                "Use for finding voters by name since original voters table doesn't have names"
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
                "street_suffix": "Street type (ST, AVE, BLVD, RD, etc.)",
                "city": "City name (UPPERCASE like 'SUMMIT', 'WESTFIELD')",
                "state": "State abbreviation (NJ)",
                "zip_code": "5-digit ZIP code (e.g., '07901')",
                "county": "County name (UPPERCASE)",
                "latitude": "Geocoded latitude (FLOAT)",
                "longitude": "Geocoded longitude (FLOAT)",
                "geo_location": "BigQuery GEOGRAPHY type for spatial queries",
                "geocoding_source": "Source of geocoding (e.g., 'GOOGLE_MAPS')",
                "geocoding_date": "When location was geocoded"
            },
            "hints": [
                "All 264K addresses have been geocoded with preserved lat/lng",
                "IMPORTANT: Use 'geo_location' field (NOT 'geo') with ST_* functions for spatial analysis",
                "Join with voters or donations using address_id",
                "To get addresses for individuals: JOIN individual_addresses ON individuals.master_id = individual_addresses.master_id THEN JOIN addresses ON individual_addresses.address_id = addresses.address_id",
                "Distance conversions: 1 mile = 1609.34 meters, 1 km = 1000 meters"
            ]
        },
        
        "donations": {
            "description": "Campaign contribution records from FEC data, partially matched to voter records",
            "primary_key": "donation_record_id",
            "foreign_keys": ["master_id", "address_id"],
            "key_fields": {
                "donation_record_id": "Unique donation identifier",
                "master_id": "Links to individuals table (NULL if unmatched - 76% are unmatched)",
                "address_id": "Links to addresses table (NULL if unmatched)",
                "committee_name": "Recipient committee/campaign name (e.g., 'HARRIS FOR PRESIDENT', 'ACTBLUE')",
                "contribution_amount": "Donation amount in dollars (NUMERIC)",
                "election_type": "Type of election (PRIMARY, GENERAL, etc.)",
                "election_year": "Year of the election (INTEGER)",
                "employer": "Donor's employer",
                "occupation": "Donor's occupation",
                "donation_date": "Date of contribution (DATE)",
                "original_full_name": "Original name from FEC record (various formats)",
                "original_address": "Original address from FEC record",
                "match_confidence": "Confidence score for voter match (0-1)",
                "match_method": "Method used for matching (exact, fuzzy, etc.)"
            },
            "hints": [
                "Only ~24% of donations matched to voter records using fuzzy matching",
                "Use original_full_name with LIKE patterns for name searches",
                "Names can be 'LASTNAME, FIRSTNAME' or 'FIRSTNAME LASTNAME' format",
                "Always search with name variations (GREG vs GREGORY, middle initials)",
                "Join with individuals using master_id to get donor details",
                "Use match_confidence to filter for high-quality matches",
                "IMPORTANT: Always query donations table for donor info, not just donor_view"
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
                "street_name": "Street name (UPPERCASE)",
                "city": "City name", 
                "county": "County name",
                "zip_code": "5-digit ZIP code",
                "republican_count": "Number of Republican voters",
                "democrat_count": "Number of Democrat voters",
                "unaffiliated_count": "Number of unaffiliated voters",
                "other_party_count": "All other parties",
                "total_voters": "Total voters on street",
                "republican_pct": "Percentage Republican (0-100)",
                "democrat_pct": "Percentage Democrat (0-100)",
                "unaffiliated_pct": "Percentage unaffiliated (0-100)",
                "street_center_location": "Geographic center of street",
                "street_center_latitude": "Center latitude",
                "street_center_longitude": "Center longitude"
            },
            "hints": [
                "Pre-calculated for streets with 3+ voters (privacy protection)",
                "Use for quick party composition analysis by geography",
                "Includes geographic center for mapping",
                "Street names are UPPERCASE for matching"
            ]
        }
    },
    
    "views": {
        "voter_geo_view": {
            "description": "RECOMMENDED: Complete voter information with all joins done for you",
            "base_tables": ["voters", "individuals", "addresses"],
            "key_fields": {
                "All fields from voters table": "Plus...",
                "standardized_name": "Full name in 'LASTNAME, FIRSTNAME' format",
                "name_first": "First name from individuals",
                "name_middle": "Middle name from individuals",
                "name_last": "Last name from individuals", 
                "standardized_address": "Full address from addresses",
                "street_number": "From addresses",
                "street_name": "From addresses",
                "city": "From addresses (USE THIS not municipal_name)",
                "zip_code": "5-digit ZIP from addresses",
                "latitude": "GPS latitude",
                "longitude": "GPS longitude",
                "geo_location": "Geography for spatial queries"
            },
            "hints": [
                "USE THIS VIEW for most voter queries - it has everything joined",
                "Includes full voter info, names, addresses, and geocoding",
                "No need to write complex joins - this view does it for you",
                "IMPORTANT: Use 'city' field not 'municipal_name' which is often NULL",
                "Search by name using: WHERE standardized_name LIKE '%LASTNAME, FIRSTNAME%'"
            ]
        },
        
        "donor_view": {
            "description": "Donation records enriched with donor and address information",
            "base_tables": ["donations", "individuals", "addresses", "voters"],
            "key_fields": {
                "All donation fields": "Plus...",
                "standardized_name": "Donor name if matched to voter",
                "standardized_address": "Donor address if matched",
                "is_registered_voter": "Boolean - donor is also a registered voter",
                "voter_party": "Party affiliation if donor is registered voter",
                "voter_county": "County if donor is registered voter",
                "city": "City from matched address",
                "latitude": "Geocoded latitude if matched",
                "longitude": "Geocoded longitude if matched"
            },
            "hints": [
                "USE THIS VIEW to analyze campaign contributions",
                "Shows which donors are also registered voters (~24% match rate)",
                "Includes geocoding for matched addresses",
                "For ALL donations including unmatched, query donations table directly"
            ]
        },
        
        "high_frequency_voters": {
            "description": "Voters who participated in 75%+ of elections since 2016",
            "hints": [
                "Pre-filtered view of consistent voters",
                "Useful for targeting likely voters",
                "Filters voters with 4+ elections participated"
            ]
        },
        
        "major_donors": {
            "description": "Individuals with total contributions > $1000",
            "key_fields": {
                "master_id": "Individual identifier",
                "standardized_name": "Donor name",
                "total_contributed": "Sum of all contributions",
                "donation_count": "Number of donations",
                "committees": "List of committees donated to"
            },
            "hints": [
                "Pre-aggregated donation amounts by individual",
                "Includes total contributions and committee counts",
                "Use for donor outreach and fundraising analysis"
            ]
        },
        
        "voter_donor_mv": {
            "description": "MATERIALIZED VIEW: Pre-joined voter and donor data for performance",
            "hints": [
                "FASTEST for donor queries - already joined",
                "Clustered by demo_party, county_name, election_year",
                "Use this instead of joining tables manually"
            ]
        },
        
        "voter_geo_summary_mv": {
            "description": "MATERIALIZED VIEW: Geographic aggregates by city/county/party",
            "key_fields": {
                "county_name": "County",
                "city": "City", 
                "demo_party": "Party",
                "voter_count": "Number of voters",
                "avg_age": "Average age",
                "participation_rate": "Average participation rate"
            },
            "hints": [
                "Pre-calculated voter counts, averages, and participation rates",
                "Clustered by county_name, city, demo_party",
                "Use for city/county level analysis"
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
        "find_voter_by_name": {
            "description": "Find voters by name (names are in individuals table, not voters)",
            "example": """
                -- BEST: Use voter_geo_view which has everything joined
                SELECT * FROM voter_data.voter_geo_view 
                WHERE standardized_name LIKE '%TUSAR, GREG%'
                AND city = 'BERNARDSVILLE'  -- Use city, not municipal_name
            """,
            "notes": "Names are 'LASTNAME, FIRSTNAME' format in standardized fields"
        },
        
        "find_all_donations_by_name": {
            "description": "Find ALL donations including those not matched to voters",
            "example": """
                -- Search original donation records (76% are unmatched)
                SELECT * FROM voter_data.donations
                WHERE UPPER(original_full_name) LIKE '%TUSAR%GREG%'
                   OR UPPER(original_full_name) LIKE '%GREG%TUSAR%'
                   
                -- Or search matched donations only
                SELECT * FROM voter_data.donor_view
                WHERE standardized_name LIKE '%TUSAR, GREG%'
            """,
            "notes": "Always try name variations (GREG vs GREGORY, with/without middle initial)"
        },
        
        "find_latino_voters": {
            "description": "Find Latino/Hispanic voters using demo_race field",
            "example": """
                SELECT * FROM voter_data.voter_geo_view
                WHERE UPPER(demo_race) LIKE '%LATINO%' 
                   OR UPPER(demo_race) LIKE '%HISPANIC%'
            """,
            "notes": "demo_race contains both race AND ethnicity information"
        },
        
        "find_voters_by_location": {
            "description": "Find voters within a certain distance of a point",
            "example": """
                -- Within 1 mile of Summit train station
                SELECT * FROM voter_data.voter_geo_view
                WHERE ST_DWITHIN(
                    geo_location, 
                    ST_GEOGPOINT(-74.3574, 40.7155), 
                    1609.34  -- 1 mile in meters
                )
            """,
            "notes": "Common landmarks: Summit Station (-74.3574, 40.7155), Westfield Downtown (-74.3473, 40.6502)"
        },
        
        "analyze_street_politics": {
            "description": "Get party composition by street",
            "example": """
                SELECT * FROM voter_data.street_party_summary
                WHERE city = 'SUMMIT' AND total_voters >= 10
                ORDER BY democrat_pct DESC
            """,
            "notes": "Pre-aggregated for performance, minimum 3 voters for privacy"
        },
        
        "high_value_democratic_donors": {
            "description": "Find major Democratic donors in a city",
            "example": """
                -- Using materialized view (FASTEST)
                SELECT * FROM voter_data.major_donors md
                JOIN voter_data.voter_geo_view v ON md.master_id = v.master_id
                WHERE v.city = 'SUMMIT' 
                AND v.demo_party = 'DEMOCRAT'
                ORDER BY total_contributed DESC
            """,
            "notes": "major_donors view pre-filters for $1000+ total contributions"
        },
        
        "donors_by_geography": {
            "description": "Find donors within a specific geographic area",
            "example": """
                -- CORRECT: Find donors within 1 mile of a location
                SELECT
                    i.standardized_name,
                    i.master_id,
                    SUM(d.contribution_amount) AS total_contributions
                FROM voter_data.donations d
                INNER JOIN voter_data.individuals i ON d.master_id = i.master_id
                INNER JOIN voter_data.individual_addresses ia ON i.master_id = ia.master_id
                INNER JOIN voter_data.addresses a ON ia.address_id = a.address_id
                WHERE ST_DWITHIN(
                    a.geo_location,  -- NOTE: Field is 'geo_location' not 'geo'
                    ST_GEOGPOINT(-74.65, 40.70),
                    1609.34  -- 1 mile in meters
                )
                AND d.master_id IS NOT NULL  -- Only matched donations
                GROUP BY i.standardized_name, i.master_id
                HAVING SUM(d.contribution_amount) > 1000
                ORDER BY total_contributions DESC
            """,
            "notes": "Must join through individual_addresses to link individuals to addresses correctly"
        },
        
        "voting_frequency_analysis": {
            "description": "Find voters by participation patterns",
            "example": """
                -- Super voters (voted in all recent elections)
                SELECT * FROM voter_data.voter_geo_view
                WHERE participation_general_2020 = TRUE 
                  AND participation_general_2022 = TRUE
                  AND participation_general_2024 = TRUE
                  AND participation_primary_2022 = TRUE
                  AND participation_primary_2024 = TRUE
            """,
            "notes": "Use high_frequency_voters view for pre-filtered consistent voters"
        },
        
        "geographic_clustering": {
            "description": "Find geographic centers of voter groups",
            "example": """
                SELECT demo_party,
                       ST_CENTROID(ST_UNION_AGG(geo_location)) as center,
                       COUNT(*) as voter_count
                FROM voter_data.voter_geo_view
                WHERE county_name = 'UNION'
                GROUP BY demo_party
            """,
            "notes": "ST_CENTROID finds geographic center, ST_UNION_AGG combines geometries"
        }
    },
    
    "important_notes": [
        "ALWAYS scope table names with 'voter_data.' prefix (e.g., 'voter_data.voters' not just 'voters')",
        "Party values must be exact: 'REPUBLICAN', 'DEMOCRAT', 'UNAFFILIATED' (case-sensitive)",
        "Congressional district stored as 'NJ CONGRESSIONAL DISTRICT 07' not 'NJ-07'",
        "demo_race field contains BOTH race AND ethnicity (e.g., Latino, Hispanic, Asian, Black, White)",
        "Names in standardized fields use 'LASTNAME, FIRSTNAME' format",
        "Always use 'city' field instead of 'municipal_name' (which has many NULLs)",
        "All 264K addresses have preserved geocoding (latitude/longitude)",
        "Only 24% of donations matched to voters - query donations table for unmatched",
        "Use voter_geo_view for most queries - it has everything pre-joined",
        "Use donor_view for donation analysis - includes voter matching",
        "Counties and cities are UPPERCASE in the database",
        "Distance functions use meters: 1 mile = 1609.34 meters",
        "Names in original voters table are CASE SENSITIVE (use UPPER() for safety)",
        "ZIP codes are stored as 5-digit strings (e.g., '07901' not 7901)"
    ],
    
    "performance_tips": [
        "Use materialized views (voter_donor_mv, voter_geo_summary_mv) for best performance",
        "Use voter_geo_view instead of joining tables manually",
        "Use ST_DWITHIN for spatial queries instead of calculating ST_DISTANCE",
        "Pre-aggregated views (street_party_summary, major_donors) are fastest for analysis",
        "Cluster your queries by demo_party, county_name when possible"
    ]
}

def format_for_llm():
    """Format the database manifest for LLM consumption"""
    output = []
    output.append("=== NJ VOTER DATABASE MANIFEST ===\n")
    output.append(DATABASE_MANIFEST["overview"])
    
    output.append("\n=== KEY TABLES ===")
    for table_name, table_info in DATABASE_MANIFEST["tables"].items():
        output.append(f"\n{table_name}: {table_info['description']}")
        if "key_fields" in table_info:
            for field, desc in list(table_info["key_fields"].items())[:5]:
                output.append(f"  - {field}: {desc}")
        if "hints" in table_info:
            output.append(f"  Hints: {table_info['hints'][0]}")
    
    output.append("\n=== RECOMMENDED VIEWS ===")
    for view_name, view_info in DATABASE_MANIFEST["views"].items():
        output.append(f"\n{view_name}: {view_info['description']}")
        if "hints" in view_info:
            output.append(f"  Key hint: {view_info['hints'][0]}")
    
    output.append("\n=== QUERY PATTERNS ===")
    for pattern_name, pattern_info in DATABASE_MANIFEST["query_patterns"].items():
        output.append(f"\n{pattern_name}: {pattern_info['description']}")
        if "notes" in pattern_info:
            output.append(f"  Note: {pattern_info['notes']}")
    
    output.append("\n=== CRITICAL REMINDERS ===")
    for note in DATABASE_MANIFEST["important_notes"][:8]:
        output.append(f"• {note}")
    
    return "\n".join(output)
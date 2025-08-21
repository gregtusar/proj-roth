# NJ Voter Data Schema Migration Plan

## Executive Summary
This plan outlines the migration from a monolithic voter table to a normalized relational database structure that separates persistent data (individuals, addresses with geocoding) from replaceable raw data sources (voter files, donation records).

## Current State
- **voters table**: 622,000+ records with embedded geocoding data (expensive to regenerate)
- **street_party_summary table**: Aggregated street-level data
- **Source files**: Available in GCS bucket `nj7voterfile`
  - `secondvoterfile.csv` - Latest voter file (August 2024) with 80 columns
  - `firstvoterfile.csv` - Original voter file (same schema)
  - `donations.csv` - Campaign contribution data

## Target Architecture

### Core Principles
1. **Data Normalization**: Separate concerns (individuals, addresses, voter records, donations)
2. **Geocoding Preservation**: Extract and preserve existing expensive geocoding data
3. **Replaceable Raw Data**: Allow voter/donation files to be easily updated
4. **Relationship Management**: Use foreign keys to maintain data integrity
5. **Fuzzy Matching**: Link records to individuals using name/address matching

### Target Schema

#### Persistent Tables (Never Dropped)

**individuals**
```sql
- master_id (STRING, PK) - UUID generated
- standardized_name (STRING) - "{last}, {first} {middle}"
- name_first (STRING)
- name_middle (STRING) 
- name_last (STRING)
- name_suffix (STRING)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**addresses**
```sql
- address_id (STRING, PK) - Hash of standardized_address
- standardized_address (STRING) - Normalized full address
- street_number (STRING)
- street_name (STRING)
- street_suffix (STRING)
- city (STRING)
- state (STRING)
- zip_code (STRING)
- county (STRING)
- geo_location (GEOGRAPHY) - Preserved from existing data
- latitude (FLOAT64)
- longitude (FLOAT64)
- geocoding_source (STRING) - 'google_maps' or 'original_import'
- geocoding_date (DATE)
- last_updated (TIMESTAMP)
```

**individual_addresses**
```sql
- individual_address_id (STRING, PK) - UUID
- master_id (STRING, FK -> individuals)
- address_id (STRING, FK -> addresses)
- address_type (STRING) - 'residential', 'mailing', 'previous'
- valid_from (DATE)
- valid_to (DATE) - NULL if current
- is_current (BOOLEAN)
- source_system (STRING) - 'voter_file', 'donation', etc.
```

#### Raw Data Tables (Replaceable)

**raw_voters**
```sql
- All 80 columns from voter CSV including:
  - Identity: id, name_first, name_middle, name_last
  - Address: addr_residential_* fields
  - Demographics: demo_age, demo_party, demo_race, demo_gender
  - Districts: congressional_name, state_house_name, etc.
  - Voting history: participation_* and vote_* for 2016-2024
  - Scores: score_support_generic_dem, current_support_score
- import_batch_id (STRING)
- import_timestamp (TIMESTAMP)
```

**raw_donations**
```sql
- All columns from donations CSV
- import_batch_id (STRING)
- import_timestamp (TIMESTAMP)
```

#### Processed Tables (Regenerated)

**voters**
```sql
- voter_record_id (STRING, PK) - UUID
- vendor_voter_id (STRING) - Original ID from raw_voters
- master_id (STRING, FK -> individuals)
- address_id (STRING, FK -> addresses)
- demo_party (STRING)
- registration_status (STRING)
- congressional_district (STRING)
- state_house_district (STRING)
- state_senate_district (STRING)
- precinct (STRING)
- municipal_name (STRING)
- county_name (STRING)
- demo_age (INT64)
- demo_race (STRING)
- demo_gender (STRING)
- voter_type (STRING)
- [voting history columns - participation_*, vote_*]
- score_support_generic_dem (FLOAT64)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**donations**
```sql
- donation_record_id (STRING, PK) - UUID
- master_id (STRING, FK -> individuals, NULL if no match)
- address_id (STRING, FK -> addresses, NULL if no match)
- committee_name (STRING)
- contribution_amount (NUMERIC)
- election_type (STRING)
- election_year (INT64)
- employer (STRING)
- occupation (STRING)
- donation_date (DATE)
- created_at (TIMESTAMP)
```

#### Views

**voter_geo_view** (Materialized)
```sql
SELECT 
  v.*,
  i.standardized_name,
  a.standardized_address,
  a.geo_location,
  a.latitude,
  a.longitude
FROM voters v
JOIN individuals i ON v.master_id = i.master_id
JOIN addresses a ON v.address_id = a.address_id
```

## Migration Process

### Phase 1: Preparation (Day 1)
1. **Backup existing data**
   - Export voters table to GCS
   - Export street_party_summary to GCS
   
2. **Create new schema**
   - Create all new tables with proper indexes
   - Set up foreign key constraints

### Phase 2: Extract Geocoding Data (Day 1)
1. **Extract unique addresses with geocoding**
   ```sql
   SELECT DISTINCT
     addr_residential_line1,
     city,
     state,
     zip_code,
     county_name,
     latitude,
     longitude,
     geo_location
   FROM voters
   WHERE latitude IS NOT NULL
   ```
   
2. **Standardize and store in addresses table**
   - Generate address_id using hash
   - Preserve all geocoding data

### Phase 3: Individual Entity Resolution (Day 2)
1. **Extract unique individuals**
   - Use fuzzy matching on name components
   - Group by standardized name format
   - Generate master_id for each unique individual

2. **Matching Strategy**
   - Exact match: first_name + last_name + address
   - Fuzzy match: Levenshtein distance < 3 for names at same address
   - Middle name/initial handling
   - Suffix handling (Jr., Sr., III, etc.)

### Phase 4: Data Loading (Day 2-3)
1. **Load raw_voters from CSV**
   - Use `secondvoterfile.csv` as source
   - Handle TRUE/FALSE string to boolean conversion
2. **Load raw_donations from CSV**
3. **Generate voters table**
   - Match each raw_voter to master_id
   - Link to address_id
   - Copy relevant columns
4. **Generate donations table**
   - Match donations to individuals where possible
   - Handle unmatched records

### Phase 5: Validation (Day 3)
1. **Data integrity checks**
   - Verify all geocoding preserved
   - Check foreign key relationships
   - Compare record counts
   - Validate sample queries

2. **Create materialized views**
3. **Update application code**

## Scripts Required

### 1. Schema Creation
- `sql/01_create_persistent_tables.sql`
- `sql/02_create_raw_tables.sql`
- `sql/03_create_processed_tables.sql`
- `sql/04_create_views.sql`

### 2. Data Extraction
- `scripts/01_backup_existing.py` - Backup current tables
- `scripts/02_extract_geocoding.py` - Extract and save geocoding data
- `scripts/03_extract_individuals.py` - Entity resolution for individuals

### 3. Data Loading
- `scripts/04_load_raw_data.py` - Load CSVs into raw tables
- `scripts/05_match_voters.py` - Link voters to individuals
- `scripts/06_match_donations.py` - Link donations to individuals

### 4. Validation
- `scripts/07_validate_migration.py` - Run validation checks
- `scripts/08_create_views.py` - Create materialized views

### 5. Utilities
- `scripts/utils/fuzzy_matcher.py` - Name matching utilities
- `scripts/utils/address_normalizer.py` - Address standardization

## Application Updates Required

### 1. Agent Configuration (`agents/nj_voter_chat_adk/config.py`)
- Update ALLOWED_TABLES to include new tables
- Add field mapping for new schema
- Update system prompt with relationship guidance

### 2. Query Examples
- Update to use joins across normalized tables
- Modify geospatial queries to use voter_geo_view

## Risk Mitigation

### Risks
1. **Geocoding Data Loss**: Critical to preserve existing geocoding
2. **Entity Resolution Errors**: Fuzzy matching may create duplicates or miss matches
3. **Performance Impact**: Joins may be slower than denormalized table
4. **Application Downtime**: Migration requires coordinated update

### Mitigations
1. **Full backup before migration**
2. **Parallel run of old and new schemas during validation**
3. **Manual review of fuzzy matching results**
4. **Performance testing with realistic queries**
5. **Rollback plan documented**

## Timeline
- **Day 0**: Review and approve plan
- **Day 1**: Backup, schema creation, geocoding extraction
- **Day 2**: Individual resolution, initial data loading
- **Day 3**: Validation, view creation, testing
- **Day 4**: Application updates, cutover
- **Day 5**: Monitoring and issue resolution

## Success Criteria
1. Zero geocoding data loss
2. All voters matched to individuals (>95% match rate)
3. Query performance within 20% of current
4. All existing application queries work with minimal modification
5. Successful load of new voter/donation files without geocoding regeneration

## Next Steps
1. Review and approve this plan
2. Create detailed SQL schemas
3. Develop migration scripts
4. Test on subset of data
5. Schedule production migration window
# NJ Voter Data Pipeline Documentation

## Overview

This document describes the complete data pipeline for the NJ Voter Data Analysis Framework, including table dependencies, update procedures, and rebuild sequences. The pipeline processes 622,000+ voter records and associated donation data to create derived analytical tables used by the conversational AI agent.

## Table Architecture

### Base Tables (Source Data)

#### 1. `proj-roth.voter_data.voters`
- **Purpose**: Core voter registration data
- **Source**: NJ voter file CSV imports
- **Update Frequency**: Monthly or as new voter files become available
- **Key Fields**:
  - `id` (voter ID)
  - Demographics (name, age, party, gender)
  - Address and geocoded location
  - Voting history (participation and party preference by year)
  - Geographic divisions (county, congressional district, precinct)
- **Size**: ~622,000 records

#### 2. `proj-roth.voter_data.raw_donations`
- **Purpose**: Political donation records
- **Source**: FEC data, campaign finance reports
- **Update Frequency**: Quarterly or as new filings available
- **Key Fields**:
  - Donor information (name, address)
  - Contribution details (amount, date, committee)
  - Employer and occupation
- **Issues**: ZIP codes often corrupted in source data

### Derived Tables (Generated from Base Tables)

#### 1. `proj-roth.voter_data.donations`
- **Purpose**: Donations matched to voter records
- **Dependencies**:
  - `voters` table (for matching)
  - `raw_donations` table (source data)
- **Generation Method**: Fuzzy matching algorithm
- **Key Features**:
  - Links donations to voter `master_id`
  - Match confidence scores (0.75-1.0)
  - Multiple matching strategies (exact, soundex, nickname)
- **Match Rate**: ~24% (despite ZIP corruption)

#### 2. `proj-roth.voter_data.street_party_summary`
- **Purpose**: Street-level political demographics
- **Dependencies**: `voters` table only
- **Generation Method**: GROUP BY aggregation
- **Key Metrics**:
  - Party counts and percentages by street
  - Geographic centroid of each street
  - Minimum 3 voters per street (privacy)
- **Use Case**: Identifying political clustering patterns

#### 3. `proj-roth.voter_data.individuals` (if exists)
- **Purpose**: Normalized individual records
- **Dependencies**: `voters` table
- **Note**: May be redundant with voters table

#### 4. `proj-roth.voter_data.addresses` (if exists)
- **Purpose**: Normalized address records
- **Dependencies**: `voters` table
- **Note**: May be redundant with voters table

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐
│  Voter File CSV │     │ Donation CSVs    │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  voters table   │     │ raw_donations    │
│  (base)         │     │ table (base)     │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │                       │
         ├───────────────────────┤
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│         donations table                  │
│   (fuzzy matched donor-voter pairs)      │
└───────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     street_party_summary table           │
│  (geographic political aggregations)      │
└───────────────────────────────────────────┘
```

## Pipeline Execution Sequence

### Phase 1: Base Table Updates

#### Step 1.1: Update Voters Table
**When**: New voter file available
**Script**: `scripts/update_voting_history.sh`
**Actions**:
1. Create timestamped backup
2. Load new CSV to staging table
3. Validate row counts and ID matches
4. Update voting history columns only
5. Preserve all geocoding and derived data
**Rationale**: Voting history changes frequently; geocoding is expensive

#### Step 1.2: Update Raw Donations Table
**When**: New FEC filings or donation data available
**Script**: Manual BigQuery import or custom script
**Actions**:
1. Import new donation CSV
2. Standardize column names
3. Clean text fields (upper case, trim)
**Rationale**: Raw data preservation for audit trail

### Phase 2: Derived Table Rebuilds

#### Step 2.1: Rebuild Donations Table
**When**: After voters or raw_donations update
**Script**: `scripts/fuzzy_match_no_zip.sql`
**Duration**: ~3-5 minutes
**Process**:
1. Create standardized temp tables with clean names
2. Run 5-stage matching algorithm:
   - Exact name + city + state (no ZIP due to corruption)
   - Exact name + state only
   - Soundex phonetic matching
   - First initial + last name
   - Nickname resolution (GREG→GREGORY)
3. Resolve duplicates (keep highest confidence)
4. Create final table with match metadata
**Rationale**: Fuzzy matching handles name variations; ignoring ZIP improves match rate

#### Step 2.2: Rebuild Street Party Summary
**When**: After voters table update
**Script**: Uncomment and run from `config/bigquery_schema.sql:191-218`
**Duration**: ~1 minute
**Process**:
1. Group voters by street address
2. Calculate party counts and percentages
3. Compute geographic centroid per street
4. Filter streets with <3 voters (privacy)
**Rationale**: Provides granular geographic political insights

### Phase 3: Validation and Quality Checks

#### Step 3.1: Validate Match Rates
```sql
-- Check donation matching statistics
SELECT
  COUNT(*) AS total_donations,
  COUNT(master_id) AS matched,
  ROUND(COUNT(master_id) * 100.0 / COUNT(*), 2) AS match_rate
FROM `proj-roth.voter_data.donations`;
```
**Expected**: 20-30% match rate

#### Step 3.2: Validate Geographic Coverage
```sql
-- Check street summary coverage
SELECT
  COUNT(DISTINCT street_name) as streets,
  COUNT(*) as street_segments,
  AVG(total_voters) as avg_voters_per_street
FROM `proj-roth.voter_data.street_party_summary`;
```

#### Step 3.3: Check Data Freshness
```sql
-- Check last update times
SELECT
  table_name,
  TIMESTAMP_MILLIS(creation_time) as created,
  TIMESTAMP_MILLIS(last_modified_time) as last_modified
FROM `proj-roth.voter_data.__TABLES__`
ORDER BY last_modified_time DESC;
```

## Automation Opportunities

### Current State
- Manual execution of individual scripts
- No dependency tracking
- No automatic validation
- No failure recovery

### Proposed Improvements

1. **Master Pipeline Script** (`scripts/rebuild_all_tables.sh`)
   - Orchestrates entire rebuild sequence
   - Handles dependencies automatically
   - Includes validation checkpoints
   - Provides rollback capability

2. **Incremental Updates**
   - Detect changed records only
   - Update affected derived records
   - Reduce processing time

3. **Scheduled Execution**
   - Cloud Scheduler for periodic updates
   - Cloud Functions for event-driven updates
   - Pub/Sub for pipeline notifications

4. **Monitoring Dashboard**
   - Table freshness metrics
   - Match rate trends
   - Data quality scores
   - Pipeline execution history

## Error Recovery Procedures

### Backup Strategy
- Always create timestamped backups before updates
- Retain backups for 30 days minimum
- Test restore procedures quarterly

### Rollback Procedures
```bash
# Rollback voters table
bq cp -f ${PROJECT_ID}:${DATASET}.voters_backup_YYYYMMDD ${PROJECT_ID}:${DATASET}.voters

# Rollback donations table
bq cp -f ${PROJECT_ID}:${DATASET}.donations_backup_YYYYMMDD ${PROJECT_ID}:${DATASET}.donations
```

### Common Issues and Fixes

1. **ZIP Code Corruption**
   - Issue: Source data has malformed ZIPs
   - Fix: Matching algorithm ignores ZIP codes
   - Impact: Slightly lower match precision

2. **Name Variations**
   - Issue: Nicknames, misspellings
   - Fix: Soundex and nickname matching
   - Impact: Improved match rate

3. **Duplicate Matches**
   - Issue: One donor matching multiple voters
   - Fix: Keep highest confidence match only
   - Impact: Conservative matching

## Performance Considerations

### Current Performance
- Full donations rebuild: 3-5 minutes
- Street summary rebuild: 1 minute
- Voters update: 2-3 minutes

### Optimization Opportunities
1. **Partition Tables**: Already implemented for donations (by month)
2. **Cluster Tables**: Implemented on key join columns
3. **Materialized Views**: Consider for frequently queried aggregations
4. **Incremental Processing**: Implement change data capture

## Security and Privacy

### Data Protection
- No PII exposed in street summaries (<3 voter threshold)
- Service accounts use minimal permissions
- Audit logging enabled in BigQuery

### Access Control
- Read-only access for application service account
- Write access restricted to pipeline service account
- No public access to raw voter data

## Maintenance Schedule

### Weekly
- Check pipeline execution logs
- Validate data freshness
- Review match rate trends

### Monthly
- Update voters table with new registrations
- Rebuild all derived tables
- Archive old backups

### Quarterly
- Update donation data from FEC
- Review and optimize matching algorithm
- Performance tuning review

## Contact and Support

- **Pipeline Owner**: Data Engineering Team
- **Documentation**: This document and `/docs/`
- **Scripts Location**: `/scripts/`
- **Monitoring**: Cloud Console → BigQuery → Dataset: voter_data

## Appendix: Quick Command Reference

```bash
# Update voters table
bash scripts/update_voting_history.sh

# Rebuild donations table
bq query --use_legacy_sql=false < scripts/fuzzy_match_no_zip.sql

# Rebuild street summary (uncomment first)
bq query --use_legacy_sql=false < config/bigquery_schema.sql

# Check table freshness
bq ls -n 1000 proj-roth:voter_data | grep -E "voters|donations|street"

# Create backup
bq cp proj-roth:voter_data.voters proj-roth:voter_data.voters_backup_$(date +%Y%m%d)
```
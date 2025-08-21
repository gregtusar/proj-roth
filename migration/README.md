# NJ Voter Data Migration

This directory contains the schema migration plan and scripts for normalizing the voter database structure.

## Overview

The migration transforms a monolithic voter table into a normalized relational structure that:
- Preserves expensive geocoding data
- Separates persistent entities (individuals, addresses) from replaceable raw data
- Enables easy updates of voter/donation files without re-geocoding
- Implements fuzzy matching for entity resolution

## Directory Structure

```
migration/
├── MIGRATION_PLAN.md       # Comprehensive migration plan
├── README.md               # This file
├── docs/                   # Additional documentation
├── sql/                    # SQL schema definitions
│   ├── 01_create_persistent_tables.sql
│   ├── 02_create_raw_tables.sql
│   ├── 03_create_processed_tables.sql
│   └── 04_create_views.sql
├── scripts/                # Migration scripts
│   ├── 01_backup_existing.py
│   ├── 02_extract_geocoding.py
│   ├── 03_extract_individuals.py (TODO)
│   ├── 04_load_raw_data.py (TODO)
│   ├── 05_match_voters.py (TODO)
│   ├── 06_match_donations.py (TODO)
│   ├── 07_validate_migration.py (TODO)
│   └── utils/
│       ├── fuzzy_matcher.py
│       └── address_normalizer.py (TODO)
```

## Quick Start

1. **Review the migration plan:**
   ```bash
   cat MIGRATION_PLAN.md
   ```

2. **Set up environment:**
   ```bash
   export GOOGLE_CLOUD_PROJECT=proj-roth
   export GOOGLE_CLOUD_REGION=us-central1
   ```

3. **Run migration (after approval):**
   ```bash
   # Step 1: Backup existing data
   python scripts/01_backup_existing.py
   
   # Step 2: Create new schema
   bq query --use_legacy_sql=false < sql/01_create_persistent_tables.sql
   bq query --use_legacy_sql=false < sql/02_create_raw_tables.sql
   bq query --use_legacy_sql=false < sql/03_create_processed_tables.sql
   
   # Step 3: Extract and preserve geocoding
   python scripts/02_extract_geocoding.py
   
   # Continue with remaining steps...
   ```

## Key Components

### Persistent Tables
- **individuals**: Unique people with master_id
- **addresses**: Unique addresses with preserved geocoding
- **individual_addresses**: Links individuals to addresses

### Raw Tables (Replaceable)
- **raw_voters**: Direct import from voter CSV
- **raw_donations**: Direct import from donations CSV

### Processed Tables (Regenerated)
- **voters**: Links raw_voters to individuals
- **donations**: Links raw_donations to individuals

### Views
- **voter_geo_view**: Materialized view for geospatial queries
- **voters_compat**: Backward compatibility with old schema

## Migration Process

1. **Backup** existing data to GCS
2. **Create** new table schema
3. **Extract** geocoding data (preserve expensive data)
4. **Resolve** individuals using fuzzy matching
5. **Load** raw data from CSVs
6. **Match** voters and donations to individuals
7. **Validate** data integrity
8. **Update** application configuration

## Testing

Before running on production:
1. Test scripts on a subset of data
2. Verify geocoding preservation
3. Check fuzzy matching accuracy
4. Validate query performance

## Rollback Plan

If issues occur:
1. Restore from backup files in GCS
2. Revert application configuration
3. Document issues for resolution

## Next Steps

1. Get approval for migration plan
2. Complete remaining migration scripts
3. Test on development dataset
4. Schedule production migration window
5. Execute migration with monitoring
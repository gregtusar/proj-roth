#!/bin/bash

# Script to update voting history columns in BigQuery voters table
# Preserves all existing data, especially geolocation tags

set -e  # Exit on error

PROJECT_ID="proj-roth"
DATASET="voter_data"
TABLE="voters"
STAGING_TABLE="voters_staging"
BACKUP_TABLE="voters_backup_$(date +%Y%m%d_%H%M%S)"
CSV_PATH="gs://nj7voterfile/voterfile_withhistory.csv"

echo "========================================"
echo "Voter Table Voting History Update Script"
echo "========================================"
echo ""

# Step 1: Create backup
echo "Step 1: Creating backup table ${BACKUP_TABLE}..."
bq cp -f ${PROJECT_ID}:${DATASET}.${TABLE} ${PROJECT_ID}:${DATASET}.${BACKUP_TABLE}
echo "✓ Backup created successfully"
echo ""

# Step 2: Create staging table and load CSV
echo "Step 2: Loading CSV into staging table..."

# Create staging table schema with correct field names and types
cat > /tmp/staging_schema.json << 'EOF'
[
  {"name": "id", "type": "STRING", "mode": "NULLABLE"},
  {"name": "participation_primary_2016", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2017", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2018", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2019", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2020", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2021", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2022", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2023", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_primary_2024", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2016", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2017", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2018", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2019", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2020", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2021", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2022", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2023", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "participation_general_2024", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2016", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2016", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2017", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2017", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2018", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2018", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2019", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2019", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2020", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2020", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2021", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2021", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2022", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2022", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2023", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2023", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_dem_2024", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_primary_rep_2024", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "vote_other_2016", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2017", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2018", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2019", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2020", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2021", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2022", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2023", "type": "STRING", "mode": "NULLABLE"},
  {"name": "vote_other_2024", "type": "STRING", "mode": "NULLABLE"}
]
EOF

# Note: You may need to adjust this based on how columns are named in your CSV
# If CSV has different column names, you might need to use --autodetect and then rename columns
echo "Loading CSV from: ${CSV_PATH}"
echo "Note: Make sure your CSV column names match the schema or use column mapping"

# Load CSV into staging table
# Using autodetect first to see what columns are in the CSV
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.${STAGING_TABLE} \
  "${CSV_PATH}"

echo "✓ CSV loaded into staging table"
echo ""

# Show the schema of the loaded table to verify column names
echo "Loaded table schema:"
bq show --schema --format=prettyjson ${PROJECT_ID}:${DATASET}.${STAGING_TABLE}
echo ""

# Step 3: Validate data
echo "Step 3: Validating data..."
bq query --use_legacy_sql=false << EOF
SELECT 
  (SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`) as current_count,
  (SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${STAGING_TABLE}\`) as staging_count,
  (SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\` v
   WHERE EXISTS (SELECT 1 FROM \`${PROJECT_ID}.${DATASET}.${STAGING_TABLE}\` s WHERE s.id = v.id)) as matching_ids
EOF
echo ""

# Step 4: Update voting history columns
echo "Step 4: Updating voting history columns..."
echo "This will ONLY update participation_*, vote_primary_*, and vote_other_* columns."
echo "All other data including geolocation will be preserved."
echo ""
read -p "Do you want to proceed with the update? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Update cancelled."
    exit 1
fi

bq query --use_legacy_sql=false << EOF
UPDATE \`${PROJECT_ID}.${DATASET}.${TABLE}\` v
SET 
  -- Update participation columns
  participation_primary_2016 = s.participation_primary_2016,
  participation_primary_2017 = s.participation_primary_2017,
  participation_primary_2018 = s.participation_primary_2018,
  participation_primary_2019 = s.participation_primary_2019,
  participation_primary_2020 = s.participation_primary_2020,
  participation_primary_2021 = s.participation_primary_2021,
  participation_primary_2022 = s.participation_primary_2022,
  participation_primary_2023 = s.participation_primary_2023,
  participation_primary_2024 = s.participation_primary_2024,
  participation_general_2016 = s.participation_general_2016,
  participation_general_2017 = s.participation_general_2017,
  participation_general_2018 = s.participation_general_2018,
  participation_general_2019 = s.participation_general_2019,
  participation_general_2020 = s.participation_general_2020,
  participation_general_2021 = s.participation_general_2021,
  participation_general_2022 = s.participation_general_2022,
  participation_general_2023 = s.participation_general_2023,
  participation_general_2024 = s.participation_general_2024,
  -- Update vote primary columns
  vote_primary_dem_2016 = s.vote_primary_dem_2016,
  vote_primary_rep_2016 = s.vote_primary_rep_2016,
  vote_primary_dem_2017 = s.vote_primary_dem_2017,
  vote_primary_rep_2017 = s.vote_primary_rep_2017,
  vote_primary_dem_2018 = s.vote_primary_dem_2018,
  vote_primary_rep_2018 = s.vote_primary_rep_2018,
  vote_primary_dem_2019 = s.vote_primary_dem_2019,
  vote_primary_rep_2019 = s.vote_primary_rep_2019,
  vote_primary_dem_2020 = s.vote_primary_dem_2020,
  vote_primary_rep_2020 = s.vote_primary_rep_2020,
  vote_primary_dem_2021 = s.vote_primary_dem_2021,
  vote_primary_rep_2021 = s.vote_primary_rep_2021,
  vote_primary_dem_2022 = s.vote_primary_dem_2022,
  vote_primary_rep_2022 = s.vote_primary_rep_2022,
  vote_primary_dem_2023 = s.vote_primary_dem_2023,
  vote_primary_rep_2023 = s.vote_primary_rep_2023,
  vote_primary_dem_2024 = s.vote_primary_dem_2024,
  vote_primary_rep_2024 = s.vote_primary_rep_2024,
  -- Update vote other columns
  vote_other_2016 = s.vote_other_2016,
  vote_other_2017 = s.vote_other_2017,
  vote_other_2018 = s.vote_other_2018,
  vote_other_2019 = s.vote_other_2019,
  vote_other_2020 = s.vote_other_2020,
  vote_other_2021 = s.vote_other_2021,
  vote_other_2022 = s.vote_other_2022,
  vote_other_2023 = s.vote_other_2023,
  vote_other_2024 = s.vote_other_2024
FROM \`${PROJECT_ID}.${DATASET}.${STAGING_TABLE}\` s
WHERE v.id = s.id
EOF

echo "✓ Voting history columns updated"
echo ""

# Step 5: Verify update
echo "Step 5: Verifying update..."
bq query --use_legacy_sql=false << EOF
SELECT 
  COUNT(*) as total_voters,
  COUNT(location) as voters_with_location,
  COUNT(participation_primary_2024) as voters_with_primary_2024,
  COUNT(participation_general_2024) as voters_with_general_2024,
  COUNT(vote_primary_dem_2024) as dem_primary_2024,
  COUNT(vote_primary_rep_2024) as rep_primary_2024
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
EOF

echo ""
echo "========================================"
echo "Update complete!"
echo "Backup table: ${PROJECT_ID}:${DATASET}.${BACKUP_TABLE}"
echo "Staging table: ${PROJECT_ID}:${DATASET}.${STAGING_TABLE}"
echo ""
echo "To rollback if needed:"
echo "bq cp -f ${PROJECT_ID}:${DATASET}.${BACKUP_TABLE} ${PROJECT_ID}:${DATASET}.${TABLE}"
echo ""
echo "To clean up staging table:"
echo "bq rm -f ${PROJECT_ID}:${DATASET}.${STAGING_TABLE}"
echo "========================================"

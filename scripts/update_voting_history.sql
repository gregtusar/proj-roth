-- Script to safely update voting history columns in voters table
-- This preserves all existing data including expensive geolocation tags

-- Step 1: Create a backup of the current voters table
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.voters_backup_20250120` AS
SELECT * FROM `proj-roth.voter_data.voters`;

-- Step 2: Create staging table for the new CSV data
-- Note: The CSV will need to have columns that map to these field names
-- The staging table uses STRING/BOOLEAN types matching the production table
CREATE OR REPLACE TABLE `proj-roth.voter_data.voters_staging` (
  id STRING,
  -- Participation columns (BOOLEAN in production)
  participation_primary_2016 BOOLEAN,
  participation_primary_2017 BOOLEAN,
  participation_primary_2018 BOOLEAN,
  participation_primary_2019 BOOLEAN,
  participation_primary_2020 BOOLEAN,
  participation_primary_2021 BOOLEAN,
  participation_primary_2022 BOOLEAN,
  participation_primary_2023 BOOLEAN,
  participation_primary_2024 BOOLEAN,
  participation_general_2016 BOOLEAN,
  participation_general_2017 BOOLEAN,
  participation_general_2018 BOOLEAN,
  participation_general_2019 BOOLEAN,
  participation_general_2020 BOOLEAN,
  participation_general_2021 BOOLEAN,
  participation_general_2022 BOOLEAN,
  participation_general_2023 BOOLEAN,
  participation_general_2024 BOOLEAN,
  -- Vote columns for primaries (BOOLEAN)
  vote_primary_dem_2016 BOOLEAN,
  vote_primary_rep_2016 BOOLEAN,
  vote_primary_dem_2017 BOOLEAN,
  vote_primary_rep_2017 BOOLEAN,
  vote_primary_dem_2018 BOOLEAN,
  vote_primary_rep_2018 BOOLEAN,
  vote_primary_dem_2019 BOOLEAN,
  vote_primary_rep_2019 BOOLEAN,
  vote_primary_dem_2020 BOOLEAN,
  vote_primary_rep_2020 BOOLEAN,
  vote_primary_dem_2021 BOOLEAN,
  vote_primary_rep_2021 BOOLEAN,
  vote_primary_dem_2022 BOOLEAN,
  vote_primary_rep_2022 BOOLEAN,
  vote_primary_dem_2023 BOOLEAN,
  vote_primary_rep_2023 BOOLEAN,
  vote_primary_dem_2024 BOOLEAN,
  vote_primary_rep_2024 BOOLEAN,
  -- Vote other columns (STRING)
  vote_other_2016 STRING,
  vote_other_2017 STRING,
  vote_other_2018 STRING,
  vote_other_2019 STRING,
  vote_other_2020 STRING,
  vote_other_2021 STRING,
  vote_other_2022 STRING,
  vote_other_2023 STRING,
  vote_other_2024 STRING
);

-- Step 3: After loading CSV to staging table, validate data
-- Check record counts match
SELECT 
  (SELECT COUNT(*) FROM `proj-roth.voter_data.voters`) as current_count,
  (SELECT COUNT(*) FROM `proj-roth.voter_data.voters_staging`) as staging_count,
  (SELECT COUNT(*) FROM `proj-roth.voter_data.voters` v
   WHERE EXISTS (SELECT 1 FROM `proj-roth.voter_data.voters_staging` s WHERE s.id = v.id)) as matching_ids;

-- Step 4: Update ONLY the participation and vote columns
UPDATE `proj-roth.voter_data.voters` v
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
FROM `proj-roth.voter_data.voters_staging` s
WHERE v.id = s.id;

-- Step 5: Verify the update
-- Check that geolocation data is still intact
SELECT 
  COUNT(*) as total_voters,
  COUNT(location) as voters_with_location,
  COUNT(participation_primary_2024) as voters_who_voted_primary_2024,
  COUNT(participation_general_2024) as voters_who_voted_general_2024
FROM `proj-roth.voter_data.voters`;

-- Optional: Drop staging table after successful update
-- DROP TABLE `proj-roth.voter_data.voters_staging`;
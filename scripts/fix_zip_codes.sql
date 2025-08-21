-- Script to fix zip code data types and restore leading zeros
-- Author: Claude
-- Date: 2025-08-21
-- Purpose: Convert zip_code fields from INTEGER to STRING and restore leading zeros for NJ zip codes

-- Step 1: Create backup tables before making changes
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.addresses_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.addresses`;

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.raw_voters_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.raw_voters`;

-- Step 2: Recreate raw_voters table with proper STRING type for zip code
-- First, load from CSV with proper schema
CREATE OR REPLACE EXTERNAL TABLE `proj-roth.voter_data.raw_voters_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://nj7voterfile/secondvoterfile.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = true
);

-- Step 3: Create new raw_voters table with corrected schema and formatted zip codes
CREATE OR REPLACE TABLE `proj-roth.voter_data.raw_voters` AS
SELECT 
  * EXCEPT(addr_residential_zip_code),
  -- Format NJ zip codes with leading zeros
  CASE 
    WHEN LENGTH(CAST(addr_residential_zip_code AS STRING)) = 4 
    THEN CONCAT('0', CAST(addr_residential_zip_code AS STRING))
    ELSE CAST(addr_residential_zip_code AS STRING)
  END AS addr_residential_zip_code
FROM `proj-roth.voter_data.raw_voters_external`;

-- Step 4: Recreate addresses table with STRING zip_code
CREATE OR REPLACE TABLE `proj-roth.voter_data.addresses_new` AS
SELECT 
  address_id,
  standardized_address,
  street_number,
  street_name,
  street_suffix,
  city,
  state,
  -- Convert zip_code to STRING with leading zeros
  CASE 
    WHEN LENGTH(CAST(zip_code AS STRING)) = 4 
    THEN CONCAT('0', CAST(zip_code AS STRING))
    ELSE CAST(zip_code AS STRING)
  END AS zip_code,
  county,
  geo_location,
  latitude,
  longitude,
  geocoding_source,
  geocoding_date,
  last_updated
FROM `proj-roth.voter_data.addresses`;

-- Step 5: Drop old addresses table and rename new one
DROP TABLE `proj-roth.voter_data.addresses`;
ALTER TABLE `proj-roth.voter_data.addresses_new` 
RENAME TO `addresses`;

-- Step 6: Recreate raw_donations with proper zip field
CREATE OR REPLACE EXTERNAL TABLE `proj-roth.voter_data.raw_donations_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://nj7voterfile/donations.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = true
);

CREATE OR REPLACE TABLE `proj-roth.voter_data.raw_donations` AS
SELECT 
  * EXCEPT(Zip),
  -- Format NJ zip codes with leading zeros
  CASE 
    WHEN LENGTH(CAST(Zip AS STRING)) = 4 
    THEN CONCAT('0', CAST(Zip AS STRING))
    ELSE CAST(Zip AS STRING)
  END AS zip
FROM `proj-roth.voter_data.raw_donations_external`;

-- Step 7: Recreate voter_geo_view with correct types
CREATE OR REPLACE VIEW `proj-roth.voter_data.voter_geo_view` AS
SELECT 
  v.voter_record_id,
  v.vendor_voter_id,
  v.master_id,
  v.address_id,
  i.standardized_name,
  i.name_first,
  i.name_middle,
  i.name_last,
  i.name_suffix,
  a.standardized_address,
  a.street_number,
  a.street_name,
  a.city,
  a.state,
  a.zip_code,  -- Now STRING type
  a.county AS address_county,
  a.geo_location,
  a.latitude,
  a.longitude,
  v.demo_party,
  v.demo_age,
  v.demo_race,
  v.demo_gender,
  v.registration_status,
  v.voter_type,
  v.congressional_district,
  v.state_house_district,
  v.state_senate_district,
  v.precinct,
  v.municipal_name,
  v.county_name,
  v.score_support_generic_dem,
  v.current_support_score,
  v.participation_primary_2016,
  v.participation_primary_2017,
  v.participation_primary_2018,
  v.participation_primary_2019,
  v.participation_primary_2020,
  v.participation_primary_2021,
  v.participation_primary_2022,
  v.participation_primary_2023,
  v.participation_primary_2024,
  v.participation_general_2016,
  v.participation_general_2017,
  v.participation_general_2018,
  v.participation_general_2019,
  v.participation_general_2020,
  v.participation_general_2021,
  v.participation_general_2022,
  v.participation_general_2023,
  v.participation_general_2024,
  v.created_at,
  v.updated_at
FROM `proj-roth.voter_data.voters` v
LEFT JOIN `proj-roth.voter_data.individuals` i ON v.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id;

-- Step 8: Recreate donor_view with correct types
CREATE OR REPLACE VIEW `proj-roth.voter_data.donor_view` AS
SELECT 
  d.donation_record_id,
  d.master_id,
  d.address_id,
  i.standardized_name,
  i.name_first,
  i.name_middle,
  i.name_last,
  a.standardized_address,
  a.city,
  a.state,
  a.zip_code,  -- Now STRING type
  a.geo_location,
  d.committee_name,
  d.contribution_amount,
  d.election_type,
  d.election_year,
  d.employer,
  d.occupation,
  d.donation_date,
  d.original_full_name,
  d.original_address,
  d.match_confidence,
  d.match_method,
  CASE WHEN v.master_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_registered_voter,
  v.demo_party AS voter_party,
  v.county_name AS voter_county
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.addresses` a ON d.address_id = a.address_id
LEFT JOIN `proj-roth.voter_data.voters` v ON d.master_id = v.master_id;

-- Step 9: Recreate materialized views
CREATE OR REPLACE MATERIALIZED VIEW `proj-roth.voter_data.voter_donor_mv` 
CLUSTER BY demo_party, county_name, election_year AS
SELECT 
  v.*,
  d.committee_name,
  d.contribution_amount,
  d.election_type,
  d.election_year,
  d.employer,
  d.occupation,
  d.donation_date
FROM `proj-roth.voter_data.voter_geo_view` v
LEFT JOIN `proj-roth.voter_data.donations` d ON v.master_id = d.master_id;

-- Step 10: Test queries to verify fix
-- Check that zip codes now have leading zeros
SELECT 
  zip_code,
  COUNT(*) as count
FROM `proj-roth.voter_data.addresses`
WHERE zip_code LIKE '07%' OR zip_code LIKE '08%'
GROUP BY zip_code
ORDER BY count DESC
LIMIT 10;

-- Verify raw_voters has correct zip codes
SELECT 
  addr_residential_zip_code,
  COUNT(*) as count
FROM `proj-roth.voter_data.raw_voters`
WHERE addr_residential_zip_code LIKE '07%' OR addr_residential_zip_code LIKE '08%'
GROUP BY addr_residential_zip_code
ORDER BY count DESC
LIMIT 10;
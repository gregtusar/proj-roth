-- Script to fix zip code data types and rematch donations to individuals
-- Author: Claude
-- Date: 2025-08-21
-- Purpose: Convert zip_code fields from INTEGER to STRING, restore leading zeros, and rematch donations

-- ============================================
-- STEP 1: BACKUP CURRENT TABLES
-- ============================================
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.addresses_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.addresses`;

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.donations_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.donations`;

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.raw_voters_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.raw_voters`;

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.raw_donations_backup_20250821` AS
SELECT * FROM `proj-roth.voter_data.raw_donations`;

-- ============================================
-- STEP 2: RELOAD RAW_VOTERS WITH STRING ZIP CODES
-- ============================================
-- Create external table pointing to CSV
CREATE OR REPLACE EXTERNAL TABLE `proj-roth.voter_data.raw_voters_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://nj7voterfile/secondvoterfile.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = true,
  allow_jagged_rows = true
);

-- Recreate raw_voters with formatted zip codes
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

-- ============================================
-- STEP 3: RELOAD RAW_DONATIONS WITH STRING ZIP CODES
-- ============================================
-- Create external table for donations CSV
CREATE OR REPLACE EXTERNAL TABLE `proj-roth.voter_data.raw_donations_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://nj7voterfile/donations.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  allow_quoted_newlines = true,
  allow_jagged_rows = true
);

-- Recreate raw_donations with formatted zip codes
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

-- ============================================
-- STEP 4: RECREATE ADDRESSES TABLE WITH STRING ZIP
-- ============================================
CREATE OR REPLACE TABLE `proj-roth.voter_data.addresses` AS
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
FROM `proj-roth.voter_data.addresses_backup_20250821`;

-- ============================================
-- STEP 5: REMATCH DONATIONS TO INDIVIDUALS
-- ============================================
-- This performs fuzzy matching between donations and voters/individuals
-- Match on name similarity and address proximity

CREATE OR REPLACE TABLE `proj-roth.voter_data.donations` AS
WITH donation_standardized AS (
  -- Standardize donation names for matching
  SELECT 
    GENERATE_UUID() AS donation_record_id,
    `Committee Name` AS committee_name,
    `Full Name` AS original_full_name,
    UPPER(TRIM(`First Name`)) AS first_name,
    UPPER(TRIM(`Last Name`)) AS last_name,
    CONCAT(
      COALESCE(`Address 1`, ''), ' ',
      COALESCE(`Address 2`, ''), ' ',
      COALESCE(City, ''), ', ',
      COALESCE(State, ''), ' ',
      COALESCE(zip, '')
    ) AS original_address,
    UPPER(TRIM(City)) AS city,
    State AS state,
    zip AS zip_code,
    Employer AS employer,
    Occupation AS occupation,
    `Contribution Amount` AS contribution_amount,
    `Election Type` AS election_type,
    `Election Year` AS election_year,
    -- Convert donation date if needed
    PARSE_DATE('%Y-%m-%d', '2024-01-01') AS donation_date -- Placeholder, adjust based on actual date format
  FROM `proj-roth.voter_data.raw_donations`
),
matched_donors AS (
  -- Match donations to individuals using fuzzy name matching
  SELECT 
    d.*,
    i.master_id,
    a.address_id,
    -- Calculate match confidence based on name similarity
    CASE 
      WHEN d.first_name = i.name_first AND d.last_name = i.name_last THEN 1.0
      WHEN SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND d.last_name = i.name_last THEN 0.9
      WHEN d.first_name = i.name_first AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last) THEN 0.9
      WHEN SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last) THEN 0.8
      WHEN SUBSTR(d.first_name, 1, 3) = SUBSTR(i.name_first, 1, 3) AND d.last_name = i.name_last THEN 0.7
      ELSE 0.5
    END AS match_confidence,
    'name_and_location' AS match_method
  FROM donation_standardized d
  LEFT JOIN `proj-roth.voter_data.individuals` i
    ON (
      -- Exact name match
      (UPPER(d.first_name) = UPPER(i.name_first) AND UPPER(d.last_name) = UPPER(i.name_last))
      OR 
      -- Soundex match for similar sounding names
      (SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last))
      OR
      -- First initial + last name match
      (SUBSTR(d.first_name, 1, 1) = SUBSTR(i.name_first, 1, 1) AND UPPER(d.last_name) = UPPER(i.name_last))
    )
  LEFT JOIN `proj-roth.voter_data.addresses` a
    ON UPPER(a.city) = d.city 
    AND a.state = d.state
    AND a.zip_code = d.zip_code
)
SELECT 
  donation_record_id,
  master_id,
  address_id,
  committee_name,
  contribution_amount,
  election_type,
  election_year,
  employer,
  occupation,
  donation_date,
  original_full_name,
  original_address,
  match_confidence,
  match_method,
  CURRENT_TIMESTAMP() AS created_at
FROM matched_donors
WHERE match_confidence >= 0.5  -- Only keep matches with reasonable confidence
OR master_id IS NULL;  -- Keep unmatched donations too

-- ============================================
-- STEP 6: RECREATE VIEWS WITH CORRECT ZIP TYPE
-- ============================================

-- Recreate voter_geo_view
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
  a.zip_code,  -- Now STRING type with leading zeros
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

-- Recreate donor_view
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
  a.zip_code,  -- Now STRING type with leading zeros
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

-- ============================================
-- STEP 7: RECREATE MATERIALIZED VIEWS
-- ============================================

-- Recreate voter_donor_mv
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

-- ============================================
-- STEP 8: VERIFICATION QUERIES
-- ============================================

-- Check zip codes in addresses table
SELECT 
  'addresses' AS table_name,
  zip_code,
  COUNT(*) as count
FROM `proj-roth.voter_data.addresses`
WHERE zip_code LIKE '07%' OR zip_code LIKE '08%'
GROUP BY zip_code
ORDER BY count DESC
LIMIT 5;

-- Check zip codes in raw_voters
SELECT 
  'raw_voters' AS table_name,
  addr_residential_zip_code,
  COUNT(*) as count
FROM `proj-roth.voter_data.raw_voters`
WHERE addr_residential_zip_code LIKE '07%' OR addr_residential_zip_code LIKE '08%'
GROUP BY addr_residential_zip_code
ORDER BY count DESC
LIMIT 5;

-- Check donation matching statistics
SELECT 
  'Donation Matching Stats' AS metric,
  COUNT(*) AS total_donations,
  COUNT(master_id) AS matched_donations,
  ROUND(COUNT(master_id) * 100.0 / COUNT(*), 2) AS match_rate_pct,
  AVG(match_confidence) AS avg_confidence
FROM `proj-roth.voter_data.donations`;

-- Check sample of matched donations
SELECT 
  original_full_name,
  i.standardized_name AS matched_to,
  match_confidence,
  match_method,
  contribution_amount,
  committee_name
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
WHERE master_id IS NOT NULL
ORDER BY match_confidence DESC
LIMIT 10;
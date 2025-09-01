-- Import New Donations File (2025-2026) with Custom Headers
-- This script handles the specific format of "2025 to 2026 cleaned.csv"
-- Date: 2025-08-30

-- ============================================
-- STEP 1: Create temporary table for new raw donations
-- ============================================

-- First, create a staging table for the new donations
CREATE OR REPLACE TABLE `proj-roth.voter_data.raw_donations_2025_2026_staging` (
  committee_name STRING,
  first_name STRING,
  middle_name STRING,
  last_name STRING,
  suffix STRING,
  address_1 STRING,
  address_2 STRING,
  city STRING,
  state STRING,
  zip STRING,
  employer STRING,
  occupation STRING,
  contribution_amount NUMERIC,
  election_type STRING,
  election_year INT64
);

-- ============================================
-- STEP 2: Load CSV data
-- Note: You'll need to load the CSV file via BigQuery UI or bq command line
-- Use this command from terminal:
-- bq load --source_format=CSV --skip_leading_rows=1 \
--   proj-roth:voter_data.raw_donations_2025_2026_staging \
--   ~/Downloads/"2025 to 2026 cleaned.csv" \
--   committee_name:STRING,first_name:STRING,middle_name:STRING,last_name:STRING,suffix:STRING,address_1:STRING,address_2:STRING,city:STRING,state:STRING,zip:STRING,employer:STRING,occupation:STRING,contribution_amount:NUMERIC,election_type:STRING,election_year:INT64
-- ============================================

-- ============================================
-- STEP 3: Append new donations to raw_donations table
-- Standardize format to match existing schema
-- ============================================

INSERT INTO `proj-roth.voter_data.raw_donations` (
  committee_name,
  full_name,
  first_name,
  middle_name,
  last_name,
  suffix,
  address_1,
  address_2,
  city,
  state,
  zip,
  employer,
  occupation,
  contribution_amount,
  election_type,
  election_year
)
SELECT 
  committee_name,
  -- Construct full_name from parts
  TRIM(CONCAT(
    COALESCE(first_name, ''), ' ',
    CASE WHEN middle_name IS NOT NULL AND LENGTH(middle_name) > 0 
         THEN CONCAT(middle_name, ' ') ELSE '' END,
    COALESCE(last_name, ''),
    CASE WHEN suffix IS NOT NULL AND LENGTH(suffix) > 0 
         THEN CONCAT(' ', suffix) ELSE '' END
  )) AS full_name,
  first_name,
  middle_name,
  last_name,
  suffix,
  address_1,
  address_2,
  city,
  state,
  zip,
  employer,
  occupation,
  contribution_amount,
  election_type,
  election_year
FROM `proj-roth.voter_data.raw_donations_2025_2026_staging`;

-- Verify the import
SELECT 
  'New donations imported' as status,
  COUNT(*) as records_added,
  MIN(election_year) as min_year,
  MAX(election_year) as max_year,
  SUM(contribution_amount) as total_amount
FROM `proj-roth.voter_data.raw_donations_2025_2026_staging`;

-- ============================================
-- STEP 4: Run the fuzzy matching algorithm
-- Using the no-ZIP version due to known ZIP code issues
-- ============================================

-- Execute the fuzzy matching script (fuzzy_match_no_zip.sql)
-- This will rebuild the donations table with all records including new ones

-- Optimized Donation-to-Voter Fuzzy Matching WITHOUT ZIP CODE REQUIREMENT
-- This version ignores zip codes due to corruption in source data

-- Create temporary indexed tables for efficient matching
CREATE OR REPLACE TEMP TABLE donor_standardized AS
SELECT 
  ROW_NUMBER() OVER() AS donor_id,
  committee_name,
  full_name AS original_full_name,
  UPPER(TRIM(first_name)) AS first_name_clean,
  UPPER(TRIM(last_name)) AS last_name_clean,
  UPPER(TRIM(COALESCE(middle_name, ''))) AS middle_name_clean,
  SUBSTR(UPPER(TRIM(first_name)), 1, 1) AS first_initial,
  SOUNDEX(UPPER(TRIM(first_name))) AS first_name_soundex,
  SOUNDEX(UPPER(TRIM(last_name))) AS last_name_soundex,
  UPPER(TRIM(city)) AS city_clean,
  state,
  zip AS zip_original,
  employer,
  occupation,
  contribution_amount,
  election_type,
  election_year,
  CONCAT(
    COALESCE(address_1, ''), ' ',
    COALESCE(address_2, ''), ' ',
    COALESCE(city, ''), ', ',
    COALESCE(state, ''), ' ',
    COALESCE(zip, '')
  ) AS original_address
FROM `proj-roth.voter_data.raw_donations`
WHERE first_name IS NOT NULL 
  AND last_name IS NOT NULL
  AND LENGTH(TRIM(first_name)) > 0
  AND LENGTH(TRIM(last_name)) > 0;

CREATE OR REPLACE TEMP TABLE individual_standardized AS
SELECT 
  i.master_id,
  UPPER(TRIM(i.name_first)) AS first_name_clean,
  UPPER(TRIM(i.name_last)) AS last_name_clean,
  UPPER(TRIM(COALESCE(i.name_middle, ''))) AS middle_name_clean,
  SUBSTR(UPPER(TRIM(i.name_first)), 1, 1) AS first_initial,
  SOUNDEX(UPPER(TRIM(i.name_first))) AS first_name_soundex,
  SOUNDEX(UPPER(TRIM(i.name_last))) AS last_name_soundex,
  UPPER(a.city) AS city_clean,
  a.state,
  a.zip_code,
  a.address_id,
  a.county
FROM `proj-roth.voter_data.individuals` i
LEFT JOIN `proj-roth.voter_data.voters` v ON i.master_id = v.master_id
LEFT JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id
WHERE i.name_first IS NOT NULL 
  AND i.name_last IS NOT NULL
  AND LENGTH(TRIM(i.name_first)) > 0
  AND LENGTH(TRIM(i.name_last)) > 0;

-- Match Stage 1: Exact Name + City + State (NO ZIP)
CREATE OR REPLACE TEMP TABLE matches_exact_city AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  1.0 AS match_confidence,
  'exact_name_city' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_clean = i.first_name_clean
  AND d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state;

-- Match Stage 2: Exact Name + State Only
CREATE OR REPLACE TEMP TABLE matches_name_state AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.85 AS match_confidence,
  'exact_name_state' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_clean = i.first_name_clean
  AND d.last_name_clean = i.last_name_clean
  AND d.state = i.state
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
WHERE e.donor_id IS NULL;

-- Match Stage 3: Soundex Name + City + State
CREATE OR REPLACE TEMP TABLE matches_soundex_city AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.80 AS match_confidence,
  'soundex_name_city' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_soundex = i.first_name_soundex
  AND d.last_name_soundex = i.last_name_soundex
  AND d.city_clean = i.city_clean
  AND d.state = i.state
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
LEFT JOIN matches_name_state n ON d.donor_id = n.donor_id
WHERE e.donor_id IS NULL 
  AND n.donor_id IS NULL;

-- Match Stage 4: First Initial + Last Name + City
CREATE OR REPLACE TEMP TABLE matches_initial_city AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.75 AS match_confidence,
  'initial_lastname_city' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_initial = i.first_initial
  AND d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
LEFT JOIN matches_name_state ns ON d.donor_id = ns.donor_id
LEFT JOIN matches_soundex_city s ON d.donor_id = s.donor_id
WHERE e.donor_id IS NULL 
  AND ns.donor_id IS NULL
  AND s.donor_id IS NULL;

-- Match Stage 5: Nickname Matching
CREATE OR REPLACE TEMP TABLE matches_nickname AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.90 AS match_confidence,
  'nickname_match' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND (
    (d.first_name_clean = 'GREG' AND i.first_name_clean = 'GREGORY')
    OR (d.first_name_clean = 'MIKE' AND i.first_name_clean = 'MICHAEL')
    OR (d.first_name_clean = 'BOB' AND i.first_name_clean = 'ROBERT')
    OR (d.first_name_clean = 'BILL' AND i.first_name_clean = 'WILLIAM')
    OR (d.first_name_clean = 'JIM' AND i.first_name_clean = 'JAMES')
    OR (d.first_name_clean = 'TOM' AND i.first_name_clean = 'THOMAS')
    OR (d.first_name_clean = 'DICK' AND i.first_name_clean = 'RICHARD')
    OR (d.first_name_clean = 'DAVE' AND i.first_name_clean = 'DAVID')
    OR (d.first_name_clean = 'DAN' AND i.first_name_clean = 'DANIEL')
    OR (d.first_name_clean = 'CHRIS' AND i.first_name_clean = 'CHRISTOPHER')
    OR (d.first_name_clean = 'MATT' AND i.first_name_clean = 'MATTHEW')
    OR (d.first_name_clean = 'STEVE' AND i.first_name_clean = 'STEPHEN')
    OR (d.first_name_clean = 'ANDY' AND i.first_name_clean = 'ANDREW')
    OR (d.first_name_clean = 'TONY' AND i.first_name_clean = 'ANTHONY')
  )
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
LEFT JOIN matches_name_state ns ON d.donor_id = ns.donor_id
LEFT JOIN matches_soundex_city s ON d.donor_id = s.donor_id
LEFT JOIN matches_initial_city ic ON d.donor_id = ic.donor_id
WHERE e.donor_id IS NULL 
  AND ns.donor_id IS NULL
  AND s.donor_id IS NULL
  AND ic.donor_id IS NULL;

-- Combine all matches
CREATE OR REPLACE TEMP TABLE all_matches AS
SELECT * FROM matches_exact_city
UNION ALL
SELECT * FROM matches_name_state
UNION ALL
SELECT * FROM matches_soundex_city
UNION ALL
SELECT * FROM matches_initial_city
UNION ALL
SELECT * FROM matches_nickname;

-- Keep best match for each donor
CREATE OR REPLACE TEMP TABLE best_matches AS
SELECT 
  donor_id,
  ARRAY_AGG(
    STRUCT(master_id, address_id, match_confidence, match_method)
    ORDER BY match_confidence DESC
    LIMIT 1
  )[OFFSET(0)].*
FROM all_matches
GROUP BY donor_id;

-- Recreate donations table with all matched and unmatched records
DROP TABLE IF EXISTS `proj-roth.voter_data.donations`;

CREATE TABLE `proj-roth.voter_data.donations`
PARTITION BY DATE_TRUNC(donation_date, MONTH)
CLUSTER BY master_id, committee_name, election_year AS
SELECT 
  GENERATE_UUID() AS donation_record_id,
  m.master_id,
  m.address_id,
  d.committee_name,
  d.contribution_amount,
  d.election_type,
  d.election_year,
  d.employer,
  d.occupation,
  -- Use current date as placeholder for new donations
  CURRENT_DATE() AS donation_date,
  d.original_full_name,
  d.original_address,
  COALESCE(m.match_confidence, 0.0) AS match_confidence,
  COALESCE(m.match_method, 'unmatched') AS match_method,
  CURRENT_TIMESTAMP() AS created_at
FROM donor_standardized d
LEFT JOIN best_matches m ON d.donor_id = m.donor_id;

-- ============================================
-- STEP 5: Update Materialized Views
-- ============================================

-- Refresh the voter_donor_mv materialized view
-- This combines voter and donation data for analytics
CALL BQ.REFRESH_MATERIALIZED_VIEW('proj-roth.voter_data.voter_donor_mv');

-- Note: The following views are automatically updated as they are regular views:
-- - donor_view (based on donations table)
-- - major_donors (based on donor_view)

-- ============================================
-- STEP 6: Verification and Statistics
-- ============================================

-- Overall matching statistics
SELECT 
  'Overall Donation Matching Statistics' AS metric,
  COUNT(*) AS total_donations,
  COUNT(master_id) AS matched_donations,
  ROUND(COUNT(master_id) * 100.0 / COUNT(*), 2) AS match_rate_pct,
  AVG(CASE WHEN master_id IS NOT NULL THEN match_confidence END) AS avg_confidence
FROM `proj-roth.voter_data.donations`;

-- Statistics for new 2025-2026 donations only
SELECT 
  '2025-2026 Donations Only' AS metric,
  COUNT(*) AS total_new_donations,
  COUNT(master_id) AS matched_new_donations,
  ROUND(COUNT(master_id) * 100.0 / COUNT(*), 2) AS match_rate_pct
FROM `proj-roth.voter_data.donations`
WHERE election_year IN (2025, 2026);

-- Match distribution by method
SELECT 
  match_method,
  COUNT(*) as count,
  ROUND(AVG(match_confidence), 3) as avg_confidence,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct_of_total
FROM `proj-roth.voter_data.donations`
WHERE election_year IN (2025, 2026)
GROUP BY match_method
ORDER BY count DESC;

-- Sample of matched records from new data
SELECT 
  original_full_name,
  i.standardized_name AS matched_voter,
  d.match_confidence,
  d.match_method,
  d.contribution_amount,
  d.committee_name,
  d.election_year,
  v.demo_party AS voter_party
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.voters` v ON d.master_id = v.master_id
WHERE d.master_id IS NOT NULL
  AND d.election_year IN (2025, 2026)
ORDER BY d.match_confidence DESC, d.contribution_amount DESC
LIMIT 20;

-- Committee summary for new data
SELECT 
  committee_name,
  COUNT(*) as donation_count,
  SUM(contribution_amount) as total_raised,
  AVG(contribution_amount) as avg_donation,
  COUNT(DISTINCT master_id) as unique_matched_donors
FROM `proj-roth.voter_data.donations`
WHERE election_year IN (2025, 2026)
GROUP BY committee_name
ORDER BY total_raised DESC;

-- ============================================
-- CLEANUP
-- ============================================
-- Once verified, you can drop the staging table:
-- DROP TABLE IF EXISTS `proj-roth.voter_data.raw_donations_2025_2026_staging`;
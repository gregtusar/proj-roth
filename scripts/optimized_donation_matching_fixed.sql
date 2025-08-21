-- Optimized Donation-to-Voter Fuzzy Matching Algorithm (Fixed)
-- Uses a multi-stage approach to efficiently match 360K donations to 620K individuals
-- Author: Claude
-- Date: 2025-08-21

-- ============================================
-- STAGE 1: Create temporary indexed tables for efficient matching
-- ============================================

-- First, create a standardized donors table with clean names and locations
CREATE OR REPLACE TEMP TABLE donor_standardized AS
SELECT 
  ROW_NUMBER() OVER() AS donor_id,
  committee_name,
  full_name AS original_full_name,
  UPPER(TRIM(first_name)) AS first_name_clean,
  UPPER(TRIM(last_name)) AS last_name_clean,
  UPPER(TRIM(COALESCE(middle_name, ''))) AS middle_name_clean,
  -- Extract first initial for matching
  SUBSTR(UPPER(TRIM(first_name)), 1, 1) AS first_initial,
  -- Create soundex codes for phonetic matching
  SOUNDEX(UPPER(TRIM(first_name))) AS first_name_soundex,
  SOUNDEX(UPPER(TRIM(last_name))) AS last_name_soundex,
  UPPER(TRIM(city)) AS city_clean,
  state,
  CASE 
    WHEN LENGTH(CAST(zip AS STRING)) = 4 
    THEN CONCAT('0', CAST(zip AS STRING))
    ELSE CAST(zip AS STRING)
  END AS zip_code,
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

-- Create a standardized individuals table with clean names and locations
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

-- ============================================
-- STAGE 2: Exact Name + Location Matches (FASTEST)
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_exact AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  1.0 AS match_confidence,
  'exact_name_location' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_clean = i.first_name_clean
  AND d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND d.zip_code = i.zip_code;

-- ============================================
-- STAGE 3: Exact Name Only (No Location Required)
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_name_only AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.85 AS match_confidence,
  'exact_name_only' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_clean = i.first_name_clean
  AND d.last_name_clean = i.last_name_clean
  AND d.state = i.state
LEFT JOIN matches_exact e ON d.donor_id = e.donor_id
WHERE e.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 4: Soundex Name + Exact Location
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_soundex AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.80 AS match_confidence,
  'soundex_name_location' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_soundex = i.first_name_soundex
  AND d.last_name_soundex = i.last_name_soundex
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND d.zip_code = i.zip_code
LEFT JOIN matches_exact e ON d.donor_id = e.donor_id
LEFT JOIN matches_name_only n ON d.donor_id = n.donor_id
WHERE e.donor_id IS NULL 
  AND n.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 5: First Initial + Last Name + Location
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_initial AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.70 AS match_confidence,
  'initial_lastname_location' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_initial = i.first_initial
  AND d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND d.zip_code = i.zip_code
LEFT JOIN matches_exact e ON d.donor_id = e.donor_id
LEFT JOIN matches_name_only n ON d.donor_id = n.donor_id
LEFT JOIN matches_soundex s ON d.donor_id = s.donor_id
WHERE e.donor_id IS NULL 
  AND n.donor_id IS NULL
  AND s.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 6: Combine All Matches
-- ============================================
CREATE OR REPLACE TEMP TABLE all_matches AS
SELECT * FROM matches_exact
UNION ALL
SELECT * FROM matches_name_only
UNION ALL
SELECT * FROM matches_soundex
UNION ALL
SELECT * FROM matches_initial;

-- ============================================
-- STAGE 7: Handle Duplicate Matches (Keep Best Match)
-- ============================================
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

-- ============================================
-- STAGE 8: Create Final Donations Table
-- ============================================
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
  CURRENT_DATE() AS donation_date, -- Placeholder, adjust if you have actual dates
  d.original_full_name,
  d.original_address,
  COALESCE(m.match_confidence, 0.0) AS match_confidence,
  COALESCE(m.match_method, 'unmatched') AS match_method,
  CURRENT_TIMESTAMP() AS created_at
FROM donor_standardized d
LEFT JOIN best_matches m ON d.donor_id = m.donor_id;

-- ============================================
-- STAGE 9: Verification and Statistics
-- ============================================

-- Get matching statistics
SELECT 
  'Donation Matching Statistics' AS metric,
  COUNT(*) AS total_donations,
  COUNT(master_id) AS matched_donations,
  ROUND(COUNT(master_id) * 100.0 / COUNT(*), 2) AS match_rate_pct,
  AVG(CASE WHEN master_id IS NOT NULL THEN match_confidence END) AS avg_confidence
FROM `proj-roth.voter_data.donations`;

-- Show match distribution by method
SELECT 
  match_method,
  COUNT(*) as count,
  ROUND(AVG(match_confidence), 3) as avg_confidence,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct_of_total
FROM `proj-roth.voter_data.donations`
GROUP BY match_method
ORDER BY count DESC;

-- Sample of high-confidence matches
SELECT 
  original_full_name,
  i.standardized_name AS matched_voter,
  d.match_confidence,
  d.match_method,
  d.contribution_amount,
  d.committee_name,
  v.demo_party AS voter_party
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.voters` v ON d.master_id = v.master_id
WHERE d.master_id IS NOT NULL
ORDER BY d.match_confidence DESC, d.contribution_amount DESC
LIMIT 20;
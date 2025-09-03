-- FIXED: Donation-to-Voter Fuzzy Matching WITHOUT ZIP CODE REQUIREMENT
-- This version removes the problematic exact_name_state matching that caused cross-city matches
-- Author: Claude (Fixed version)
-- Date: 2025-01-03

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
  -- Keep original zip for reference but don't use for matching
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
-- STAGE 2: Exact Name + City + State (NO ZIP REQUIRED)
-- ============================================
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
  -- ZIP NOT REQUIRED

-- ============================================
-- STAGE 3: Nickname Matching WITH CITY (GREG->GREGORY, etc)
-- MOVED UP in priority since it requires city match
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_nickname AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.90 AS match_confidence,
  'nickname_match_city' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND (
    -- Common nickname mappings
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
    -- Reverse mappings
    OR (d.first_name_clean = 'GREGORY' AND i.first_name_clean = 'GREG')
    OR (d.first_name_clean = 'MICHAEL' AND i.first_name_clean = 'MIKE')
    OR (d.first_name_clean = 'ROBERT' AND i.first_name_clean = 'BOB')
    OR (d.first_name_clean = 'WILLIAM' AND i.first_name_clean = 'BILL')
    OR (d.first_name_clean = 'JAMES' AND i.first_name_clean = 'JIM')
    OR (d.first_name_clean = 'THOMAS' AND i.first_name_clean = 'TOM')
    OR (d.first_name_clean = 'RICHARD' AND i.first_name_clean = 'DICK')
    OR (d.first_name_clean = 'DAVID' AND i.first_name_clean = 'DAVE')
    OR (d.first_name_clean = 'DANIEL' AND i.first_name_clean = 'DAN')
    OR (d.first_name_clean = 'CHRISTOPHER' AND i.first_name_clean = 'CHRIS')
    OR (d.first_name_clean = 'MATTHEW' AND i.first_name_clean = 'MATT')
    OR (d.first_name_clean = 'STEPHEN' AND i.first_name_clean = 'STEVE')
    OR (d.first_name_clean = 'ANDREW' AND i.first_name_clean = 'ANDY')
    OR (d.first_name_clean = 'ANTHONY' AND i.first_name_clean = 'TONY')
  )
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
WHERE e.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 4: Soundex Name + City + State (NO ZIP)
-- ============================================
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
LEFT JOIN matches_nickname n ON d.donor_id = n.donor_id
WHERE e.donor_id IS NULL 
  AND n.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 5: First Initial + Last Name + City (NO ZIP)
-- ============================================
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
LEFT JOIN matches_nickname nn ON d.donor_id = nn.donor_id
LEFT JOIN matches_soundex_city s ON d.donor_id = s.donor_id
WHERE e.donor_id IS NULL 
  AND nn.donor_id IS NULL
  AND s.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 6: REMOVED exact_name_state matching
-- This was causing false matches across different cities
-- ============================================
-- The previous script had this stage which matched:
-- - Exact first name
-- - Exact last name  
-- - Same state
-- - NO CITY REQUIREMENT (this was the problem!)
-- This resulted in 100% incorrect city matches

-- ============================================
-- STAGE 7: Middle Name + Last Name + City (for unique middle names)
-- New stage to catch people who go by middle names
-- ============================================
CREATE OR REPLACE TEMP TABLE matches_middle_name_city AS
SELECT 
  d.donor_id,
  i.master_id,
  i.address_id,
  0.70 AS match_confidence,
  'middle_lastname_city' AS match_method
FROM donor_standardized d
INNER JOIN individual_standardized i
  ON d.first_name_clean = i.middle_name_clean  -- Donor's first name matches voter's middle name
  AND d.last_name_clean = i.last_name_clean
  AND d.city_clean = i.city_clean
  AND d.state = i.state
  AND LENGTH(i.middle_name_clean) > 2  -- Avoid single initials
LEFT JOIN matches_exact_city e ON d.donor_id = e.donor_id
LEFT JOIN matches_nickname nn ON d.donor_id = nn.donor_id
LEFT JOIN matches_soundex_city s ON d.donor_id = s.donor_id
LEFT JOIN matches_initial_city ic ON d.donor_id = ic.donor_id
WHERE e.donor_id IS NULL 
  AND nn.donor_id IS NULL
  AND s.donor_id IS NULL
  AND ic.donor_id IS NULL; -- Not already matched

-- ============================================
-- STAGE 8: Combine All Matches
-- ============================================
CREATE OR REPLACE TEMP TABLE all_matches AS
SELECT * FROM matches_exact_city
UNION ALL
SELECT * FROM matches_nickname
UNION ALL
SELECT * FROM matches_soundex_city
UNION ALL
SELECT * FROM matches_initial_city
UNION ALL
SELECT * FROM matches_middle_name_city;

-- ============================================
-- STAGE 9: Handle Duplicate Matches (Keep Best Match)
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
-- STAGE 10: Create Final Donations Table
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
-- STAGE 11: Verification and Statistics
-- ============================================

-- Get matching statistics
SELECT 
  'Donation Matching Statistics (Fixed - No cross-city matches)' AS metric,
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

-- Verify no cross-city matches for LEITNER, JAMES
SELECT 
  'LEITNER, JAMES City Match Verification' as check_type,
  d.original_full_name,
  REGEXP_EXTRACT(d.original_address, r'([A-Z ]+), [A-Z]{2}') AS donor_city,
  i.standardized_name AS matched_voter,
  a.city AS voter_city,
  d.match_method,
  d.match_confidence
FROM `proj-roth.voter_data.donations` d
LEFT JOIN `proj-roth.voter_data.individuals` i ON d.master_id = i.master_id
LEFT JOIN `proj-roth.voter_data.voters` v ON d.master_id = v.master_id
LEFT JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id
WHERE d.original_full_name LIKE '%LEITNER%JAMES%'
  AND d.master_id IS NOT NULL
LIMIT 20;

-- Check overall city match accuracy
WITH donor_cities AS (
  SELECT 
    d.master_id,
    d.match_method,
    UPPER(TRIM(REGEXP_EXTRACT(d.original_address, r'([A-Z ]+), [A-Z]{2}'))) AS donor_city
  FROM `proj-roth.voter_data.donations` d
  WHERE d.master_id IS NOT NULL
),
voter_cities AS (
  SELECT 
    v.master_id,
    UPPER(a.city) AS voter_city
  FROM `proj-roth.voter_data.voters` v
  JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id
)
SELECT 
  dc.match_method,
  COUNT(*) as total_matches,
  COUNTIF(dc.donor_city = vc.voter_city) as city_matches,
  ROUND(COUNTIF(dc.donor_city = vc.voter_city) * 100.0 / COUNT(*), 2) as city_match_rate_pct
FROM donor_cities dc
JOIN voter_cities vc ON dc.master_id = vc.master_id
WHERE dc.donor_city IS NOT NULL AND vc.voter_city IS NOT NULL
GROUP BY dc.match_method
ORDER BY total_matches DESC;
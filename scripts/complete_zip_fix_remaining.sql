-- Remaining steps to complete the zip code fix and donation matching

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
    CASE 
      WHEN LENGTH(CAST(zip AS STRING)) = 4 
      THEN CONCAT('0', CAST(zip AS STRING))
      ELSE CAST(zip AS STRING)
    END AS zip_code,
    Employer AS employer,
    Occupation AS occupation,
    CAST(`Contribution Amount` AS NUMERIC) AS contribution_amount,
    `Election Type` AS election_type,
    `Election Year` AS election_year,
    -- Convert donation date if needed
    CURRENT_DATE() AS donation_date -- Placeholder, adjust based on actual date format
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
      WHEN d.first_name = UPPER(i.name_first) AND d.last_name = UPPER(i.name_last) THEN 1.0
      WHEN SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND d.last_name = UPPER(i.name_last) THEN 0.9
      WHEN d.first_name = UPPER(i.name_first) AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last) THEN 0.9
      WHEN SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last) THEN 0.8
      WHEN SUBSTR(d.first_name, 1, 3) = SUBSTR(UPPER(i.name_first), 1, 3) AND d.last_name = UPPER(i.name_last) THEN 0.7
      ELSE 0.5
    END AS match_confidence,
    'name_and_location' AS match_method
  FROM donation_standardized d
  LEFT JOIN `proj-roth.voter_data.individuals` i
    ON (
      -- Exact name match
      (d.first_name = UPPER(i.name_first) AND d.last_name = UPPER(i.name_last))
      OR 
      -- Soundex match for similar sounding names
      (SOUNDEX(d.first_name) = SOUNDEX(i.name_first) AND SOUNDEX(d.last_name) = SOUNDEX(i.name_last))
      OR
      -- First initial + last name match
      (SUBSTR(d.first_name, 1, 1) = SUBSTR(UPPER(i.name_first), 1, 1) AND d.last_name = UPPER(i.name_last))
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
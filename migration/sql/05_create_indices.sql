-- Create indices for optimized query performance
-- BigQuery automatically creates clustered tables which are more efficient than traditional indices
-- We'll use clustering and partitioning strategies for optimal performance

-- 1. INDIVIDUALS TABLE - Optimize for name lookups
CREATE OR REPLACE TABLE `proj-roth.voter_data.individuals` 
CLUSTER BY master_id, standardized_name, name_last, name_first
AS SELECT * FROM `proj-roth.voter_data.individuals`;

-- 2. ADDRESSES TABLE - Optimize for geographic and location lookups
CREATE OR REPLACE TABLE `proj-roth.voter_data.addresses`
CLUSTER BY address_id, city, county, zip_code
AS SELECT * FROM `proj-roth.voter_data.addresses`;

-- 3. VOTERS TABLE - Optimize for joins and party/demographic queries
CREATE OR REPLACE TABLE `proj-roth.voter_data.voters`
CLUSTER BY master_id, address_id, vendor_voter_id, demo_party
AS SELECT * FROM `proj-roth.voter_data.voters`;

-- 4. DONATIONS TABLE - Optimize for donor lookups and amount queries
CREATE OR REPLACE TABLE `proj-roth.voter_data.donations`
PARTITION BY DATE_TRUNC(donation_date, MONTH)
CLUSTER BY master_id, committee_name, election_year
AS SELECT * FROM `proj-roth.voter_data.donations`
WHERE donation_date IS NOT NULL;

-- Add donations without dates (no partitioning)
INSERT INTO `proj-roth.voter_data.donations`
SELECT * FROM `proj-roth.voter_data.donations`
WHERE donation_date IS NULL;

-- 5. Create search indices for commonly used fields
-- BigQuery uses search indexes for substring and full-text search

-- Create search index on names for fuzzy matching
CREATE SEARCH INDEX individuals_name_search
ON `proj-roth.voter_data.individuals`(standardized_name, name_first, name_last);

-- Create search index on addresses for address searches
CREATE SEARCH INDEX addresses_search
ON `proj-roth.voter_data.addresses`(standardized_address, street_name, city);

-- Create search index on committee names for donation searches
CREATE SEARCH INDEX donations_committee_search
ON `proj-roth.voter_data.donations`(committee_name, employer, occupation);

-- 6. Create materialized views for expensive joins
-- These pre-compute common join patterns for faster access

-- Materialized view for voter-donor joins (most expensive operation)
CREATE MATERIALIZED VIEW `proj-roth.voter_data.voter_donor_mv`
PARTITION BY DATE_TRUNC(donation_date, MONTH)
CLUSTER BY v.demo_party, v.county_name, d.election_year
AS
SELECT 
    v.voter_record_id,
    v.vendor_voter_id,
    v.master_id,
    v.address_id,
    i.standardized_name,
    i.name_first,
    i.name_last,
    a.city,
    a.county,
    a.zip_code,
    a.latitude,
    a.longitude,
    v.demo_party,
    v.demo_age,
    v.demo_gender,
    v.county_name,
    v.congressional_district,
    v.participation_general_2020,
    v.participation_general_2022,
    v.participation_general_2024,
    d.donation_record_id,
    d.committee_name,
    d.contribution_amount,
    d.election_year,
    d.donation_date,
    d.employer,
    d.occupation
FROM `proj-roth.voter_data.voters` v
JOIN `proj-roth.voter_data.individuals` i ON v.master_id = i.master_id
JOIN `proj-roth.voter_data.addresses` a ON v.address_id = a.address_id
LEFT JOIN `proj-roth.voter_data.donations` d ON v.master_id = d.master_id;

-- Materialized view for geographic queries (common distance calculations)
CREATE MATERIALIZED VIEW `proj-roth.voter_data.voter_geo_summary_mv`
CLUSTER BY county_name, city, demo_party
AS
SELECT 
    county_name,
    city,
    demo_party,
    COUNT(*) as voter_count,
    AVG(demo_age) as avg_age,
    AVG(latitude) as center_lat,
    AVG(longitude) as center_lng,
    ST_CENTROID(ST_UNION_AGG(ST_GEOGPOINT(longitude, latitude))) as geo_center,
    COUNTIF(participation_general_2024 = TRUE) as voted_2024,
    COUNTIF(participation_general_2022 = TRUE) as voted_2022,
    COUNTIF(participation_general_2020 = TRUE) as voted_2020
FROM `proj-roth.voter_data.voter_geo_view`
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
GROUP BY county_name, city, demo_party;

-- 7. Statistics for query optimization
-- Update table statistics for better query planning
ANALYZE TABLE `proj-roth.voter_data.individuals`;
ANALYZE TABLE `proj-roth.voter_data.addresses`;
ANALYZE TABLE `proj-roth.voter_data.voters`;
ANALYZE TABLE `proj-roth.voter_data.donations`;

-- 8. Create additional optimized views for common query patterns

-- High-frequency voters view (people who vote regularly)
CREATE OR REPLACE VIEW `proj-roth.voter_data.high_frequency_voters` AS
SELECT *
FROM `proj-roth.voter_data.voter_geo_view`
WHERE (
    CAST(participation_general_2024 AS INT64) +
    CAST(participation_general_2022 AS INT64) +
    CAST(participation_general_2020 AS INT64) +
    CAST(participation_primary_2024 AS INT64) +
    CAST(participation_primary_2022 AS INT64) +
    CAST(participation_primary_2020 AS INT64)
) >= 4;

-- Major donors view (high-value contributors)
CREATE OR REPLACE VIEW `proj-roth.voter_data.major_donors` AS
SELECT 
    master_id,
    standardized_name,
    city,
    voter_party,
    SUM(contribution_amount) as total_contributed,
    COUNT(*) as donation_count,
    MAX(contribution_amount) as max_contribution,
    STRING_AGG(DISTINCT committee_name LIMIT 5) as committees
FROM `proj-roth.voter_data.donor_view`
WHERE master_id IS NOT NULL
GROUP BY master_id, standardized_name, city, voter_party
HAVING SUM(contribution_amount) > 1000
ORDER BY total_contributed DESC;
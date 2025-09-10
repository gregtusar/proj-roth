-- Migration script to remove redundant columns from pdl_enrichment table
-- and rely solely on pdl_data JSON field as the single source of truth

-- Step 1: Create a new table with the clean schema
CREATE OR REPLACE TABLE `proj-roth.voter_data.pdl_enrichment_clean` AS
SELECT 
  master_id,
  pdl_id,
  likelihood,
  pdl_data,  -- This is the single source of truth
  has_email,
  has_phone,
  has_linkedin,
  has_job_info,
  has_education,
  enriched_at,
  api_version,
  min_likelihood,
  request_params
FROM `proj-roth.voter_data.pdl_enrichment`;

-- Step 2: Create a view that provides the commonly accessed fields
-- This gives us the convenience of column access without data duplication
CREATE OR REPLACE VIEW `proj-roth.voter_data.pdl_enrichment_view` AS
SELECT 
  master_id,
  pdl_id,
  likelihood,
  pdl_data,
  
  -- Extract commonly used fields from JSON for convenience
  JSON_EXTRACT_SCALAR(pdl_data, '$.full_name') as full_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.first_name') as first_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.last_name') as last_name,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_title') as job_title,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_name') as job_company,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_title_role') as job_title_role,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_title_sub_role') as job_title_sub_role,
  JSON_EXTRACT_SCALAR(pdl_data, '$.job_company_industry') as job_company_industry,
  
  -- Location fields from JSON
  JSON_EXTRACT_SCALAR(pdl_data, '$.location_city') as location_city,
  JSON_EXTRACT_SCALAR(pdl_data, '$.location_region') as location_state,
  JSON_EXTRACT_SCALAR(pdl_data, '$.location_postal_code') as location_zip,
  
  -- Boolean flags
  has_email,
  has_phone,
  has_linkedin,
  has_job_info,
  has_education,
  
  -- Metadata
  enriched_at,
  api_version,
  min_likelihood,
  request_params,
  
  -- Calculate age of enrichment
  DATE_DIFF(CURRENT_DATE(), DATE(enriched_at), DAY) as age_days
  
FROM `proj-roth.voter_data.pdl_enrichment_clean`;

-- Step 3: Rename tables (after testing)
-- IMPORTANT: Only run these after verifying the new table and view work correctly!
/*
-- Backup original table
ALTER TABLE `proj-roth.voter_data.pdl_enrichment` 
RENAME TO `proj-roth.voter_data.pdl_enrichment_old_backup`;

-- Rename clean table to main table name
ALTER TABLE `proj-roth.voter_data.pdl_enrichment_clean` 
RENAME TO `proj-roth.voter_data.pdl_enrichment`;
*/

-- Step 4: Update the ALLOWED_TABLES in the agent config to include the view
-- Add: f"{PROJECT_ID}.{DATASET}.pdl_enrichment_view"
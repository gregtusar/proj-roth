-- Drop the existing table and recreate with JSON storage schema
-- This stores the complete PDL API response for maximum flexibility

DROP TABLE IF EXISTS `proj-roth.voter_data.pdl_enrichment`;

CREATE TABLE `proj-roth.voter_data.pdl_enrichment` (
    master_id STRING NOT NULL,
    pdl_id STRING,
    likelihood FLOAT64,
    
    -- Store the complete PDL response as JSON
    pdl_data JSON NOT NULL,
    
    -- Key fields extracted for indexing/filtering
    -- These are duplicated from JSON for query performance
    has_email BOOL,
    has_phone BOOL,
    has_linkedin BOOL,
    has_job_info BOOL,
    has_education BOOL,
    
    -- Location for geographic queries
    location_city STRING,
    location_state STRING,
    location_zip STRING,
    
    -- Job info for professional targeting
    job_title STRING,
    job_company STRING,
    
    -- Metadata
    enriched_at TIMESTAMP NOT NULL,
    api_version STRING,
    min_likelihood INT64,  -- The threshold used for this match
    
    -- Request parameters used (for debugging/auditing)
    request_params JSON
)
PARTITION BY DATE(enriched_at)
CLUSTER BY master_id;

-- Add description
ALTER TABLE `proj-roth.voter_data.pdl_enrichment`
SET OPTIONS(
    description = "People Data Labs enrichment data with full JSON response storage. Key fields are extracted for indexing while complete data is preserved in pdl_data column."
);
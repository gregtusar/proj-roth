-- Create table for storing all user prompts and agent responses
CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.prompt_history` (
  prompt_id STRING NOT NULL,
  user_id STRING NOT NULL,
  user_email STRING NOT NULL,
  session_id STRING,
  prompt_text STRING NOT NULL,
  response_text STRING,
  advisor_persona STRING, -- Which advisor responded (Elon, Zohran, Susie, Tara, Jen)
  tools_used ARRAY<STRING>, -- List of tools used (bigquery_select, geocode_address, etc.)
  sql_queries ARRAY<STRING>, -- Any SQL queries executed
  row_count INTEGER, -- Number of rows returned if query was run
  error_message STRING, -- Any errors encountered
  prompt_timestamp TIMESTAMP NOT NULL,
  response_timestamp TIMESTAMP,
  response_time_ms INTEGER, -- Time taken to generate response in milliseconds
  client_type STRING, -- 'streamlit', 'cli', 'react', etc.
  ip_address STRING,
  user_agent STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(prompt_timestamp)
CLUSTER BY user_id, user_email, prompt_timestamp;
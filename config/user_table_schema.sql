-- BigQuery schema for authorized users table
-- Table: proj-roth.voter_data.authorized_users

CREATE TABLE IF NOT EXISTS `proj-roth.voter_data.authorized_users` (
  user_id STRING NOT NULL,  -- UUID for internal user identification
  email STRING NOT NULL,     -- Google email address (primary key)
  google_id STRING,          -- Google account ID
  full_name STRING,          -- User's full name from Google
  given_name STRING,         -- First name
  family_name STRING,        -- Last name
  picture_url STRING,        -- Profile picture URL from Google
  locale STRING,             -- User's locale/language preference
  is_active BOOLEAN DEFAULT TRUE,  -- Whether user has access
  role STRING DEFAULT 'viewer',    -- User role (viewer, analyst, admin)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  last_login TIMESTAMP,
  login_count INT64 DEFAULT 0,
  metadata JSON,             -- Additional Google profile data
  PRIMARY KEY (email) NOT ENFORCED
)
PARTITION BY DATE(created_at)
CLUSTER BY email;

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_id ON `proj-roth.voter_data.authorized_users`(user_id);

-- Initial admin user (replace with your email)
-- INSERT INTO `proj-roth.voter_data.authorized_users` (
--   user_id,
--   email,
--   full_name,
--   is_active,
--   role
-- ) VALUES (
--   GENERATE_UUID(),
--   'admin@example.com',
--   'Admin User',
--   TRUE,
--   'admin'
-- );
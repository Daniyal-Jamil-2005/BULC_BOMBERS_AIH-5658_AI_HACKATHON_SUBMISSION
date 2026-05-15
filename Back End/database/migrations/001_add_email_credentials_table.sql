-- Migration: Add email_credentials table
-- Date: 2025-01-15
-- Description: Add email_credentials table to replace oauth_tokens for Gmail/Outlook scanning

-- Create email_credentials table
CREATE TABLE IF NOT EXISTS email_credentials (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  provider VARCHAR(50) NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  credentials JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_provider_email (user_id, provider)
);

-- Add index for performance
CREATE INDEX idx_email_credentials_user ON email_credentials(user_id, provider);

-- Note: oauth_tokens table is deprecated but not dropped for backward compatibility
-- To migrate existing oauth_tokens data to email_credentials, run:
-- INSERT INTO email_credentials (id, user_id, provider, email_address, credentials, created_at)
-- SELECT 
--   UUID() as id,
--   user_id,
--   provider,
--   '' as email_address,  -- Must be filled in manually
--   JSON_OBJECT('access_token', access_token, 'refresh_token', refresh_token, 'expires_at', expires_at) as credentials,
--   created_at
-- FROM oauth_tokens
-- WHERE NOT EXISTS (
--   SELECT 1 FROM email_credentials ec 
--   WHERE ec.user_id = oauth_tokens.user_id AND ec.provider = oauth_tokens.provider
-- );

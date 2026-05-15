-- MySQL Schema for Inbox Copilot
-- This file contains all table definitions for the application

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  degree VARCHAR(255),
  semester INT,
  cgpa DECIMAL(3,2),
  skills JSON,
  preferred_opportunity_types JSON,
  location_preference VARCHAR(255),
  financial_need BOOLEAN DEFAULT FALSE,
  total_semesters INT DEFAULT 8
);

-- Scan history table
CREATE TABLE IF NOT EXISTS scan_history (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ranked_count INT,
  discarded_count INT,
  failed_count INT,
  results JSON,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Saved opportunities (bookmarks)
CREATE TABLE IF NOT EXISTS saved_opportunities (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  opportunity_id VARCHAR(255) NOT NULL,
  title TEXT NOT NULL,
  org VARCHAR(255),
  type VARCHAR(100),
  deadline_iso VARCHAR(50),
  score INT,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  opportunity_data JSON,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_opportunity (user_id, opportunity_id)
);

-- Checklists
CREATE TABLE IF NOT EXISTS checklists (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  opportunity_id VARCHAR(255) NOT NULL,
  task TEXT NOT NULL,
  done BOOLEAN DEFAULT FALSE,
  priority INT DEFAULT 3,
  completed_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_opp_task (user_id, opportunity_id, task(255))
);

-- Analytics aggregates (pre-computed for performance)
CREATE TABLE IF NOT EXISTS analytics_aggregates (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  period VARCHAR(50),
  total_scans INT,
  total_opportunities INT,
  avg_score DECIMAL(5,2),
  top_skills JSON,
  type_distribution JSON,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- OAuth tokens (encrypted) - DEPRECATED: Use email_credentials instead
CREATE TABLE IF NOT EXISTS oauth_tokens (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36),
  provider VARCHAR(50) NOT NULL,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_provider (user_id, provider)
);

-- Email credentials (for Gmail/Outlook scanning)
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

-- Indexes for performance
CREATE INDEX idx_scan_history_user_date ON scan_history(user_id, scanned_at DESC);
CREATE INDEX idx_saved_opportunities_user ON saved_opportunities(user_id);
CREATE INDEX idx_checklists_user_opp ON checklists(user_id, opportunity_id);
CREATE INDEX idx_email_credentials_user ON email_credentials(user_id, provider);

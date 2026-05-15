-- Migration: Add authentication columns to users table
-- Adds name and password_hash for real MySQL auth

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS name VARCHAR(255) AFTER email,
  ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) AFTER name;

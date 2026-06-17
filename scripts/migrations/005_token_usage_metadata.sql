-- Token usage explainability metadata (reference DDL; applied at startup via token_queries.py)
-- Requires: 002_token_usage.sql

ALTER TABLE token_usage
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

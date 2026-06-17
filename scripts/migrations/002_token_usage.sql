-- Token billing (reference DDL; applied at startup via app/db/token_queries.py)
-- Requires: 001_multi_user.sql

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS token_balance BIGINT NOT NULL DEFAULT 10000;

CREATE TABLE IF NOT EXISTS token_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tokens_used BIGINT NOT NULL CHECK (tokens_used > 0),
  endpoint TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_usage_user_created
  ON token_usage (user_id, created_at DESC);

-- Weighted rate limit hits for token spend tracking (reference DDL)
-- Applied at startup via app/core/rate_limit.py

ALTER TABLE rate_limit_hits
  ADD COLUMN IF NOT EXISTS weight BIGINT NOT NULL DEFAULT 1;

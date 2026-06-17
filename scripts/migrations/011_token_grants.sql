-- Token grants ledger (subscription / payment / bonus)
-- Reference DDL; applied at startup via app/db/token_grant_queries.py

CREATE TABLE IF NOT EXISTS token_grants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount BIGINT NOT NULL CHECK (amount > 0),
  source TEXT NOT NULL CHECK (source IN ('subscription', 'payment', 'bonus')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_grants_user_created
  ON token_grants (user_id, created_at DESC);

-- Chat run persistence (reference DDL; applied at startup via app/db/chat_queries.py)
-- Requires: 001_multi_user.sql

CREATE TABLE IF NOT EXISTS chat_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_key TEXT NOT NULL,
  status TEXT NOT NULL,
  generation INT NOT NULL DEFAULT 1,
  error TEXT,
  assistant_text TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, session_key)
);

CREATE INDEX IF NOT EXISTS idx_chat_runs_user_updated
  ON chat_runs (user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_runs_user_status
  ON chat_runs (user_id, status);

CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES chat_runs(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_run_created
  ON chat_messages (run_id, created_at);

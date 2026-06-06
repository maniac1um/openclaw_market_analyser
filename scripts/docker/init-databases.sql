CREATE USER openclaw_app WITH PASSWORD '7f8e1822e369bb8e8bcf1ce289bcd6c8';
CREATE DATABASE openclaw_app OWNER openclaw_app;
CREATE USER openclaw_monitor WITH PASSWORD '7f8e1822e369bb8e8bcf1ce289bcd6c8';
CREATE DATABASE openclaw_monitor OWNER openclaw_monitor;
CREATE USER openclaw_news WITH PASSWORD '7f8e1822e369bb8e8bcf1ce289bcd6c8';
CREATE DATABASE openclaw_news OWNER openclaw_news;

\c openclaw_app
CREATE TABLE IF NOT EXISTS reports (
  id BIGSERIAL PRIMARY KEY,
  ingest_id UUID NOT NULL UNIQUE,
  task_id TEXT,
  keyword TEXT NOT NULL,
  status TEXT CHECK (status IN ('queued','processing','published','failed')),
  generated_title TEXT,
  generated_at TIMESTAMPTZ,
  payload_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE reports OWNER TO openclaw_app;

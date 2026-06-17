-- Notification event types (reference DDL; applied at startup via notification_queries.py)
-- Requires: 004_notifications.sql

ALTER TABLE notifications
  ADD COLUMN IF NOT EXISTS notification_type TEXT;

CREATE INDEX IF NOT EXISTS idx_notifications_type_target_created
  ON notifications (notification_type, target, created_at DESC);

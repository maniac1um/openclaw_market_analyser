-- Payment orders: amount (fiat minor units) + tokens (credit on success)
-- Reference DDL; applied at startup via app/db/payment_queries.py

ALTER TABLE payments
  ADD COLUMN IF NOT EXISTS tokens BIGINT;

UPDATE payments
SET tokens = amount
WHERE tokens IS NULL;

ALTER TABLE payments
  ALTER COLUMN tokens SET DEFAULT 0;

-- Migrate legacy status name
UPDATE payments SET status = 'success' WHERE status = 'completed';

ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_status_check;
ALTER TABLE payments
  ADD CONSTRAINT payments_status_check
  CHECK (status IN ('pending', 'success', 'failed'));

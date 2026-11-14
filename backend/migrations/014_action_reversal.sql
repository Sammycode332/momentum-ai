BEGIN;
SET LOCAL lock_timeout='5s';
ALTER TABLE momentum_actions DROP CONSTRAINT momentum_actions_status_check;
ALTER TABLE momentum_actions ADD CONSTRAINT momentum_actions_status_check
 CHECK(status IN ('pending','applied','rejected','reverted'));
ALTER TABLE momentum_actions ADD COLUMN reverted_at timestamptz;
COMMIT;

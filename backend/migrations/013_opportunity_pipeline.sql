BEGIN;
SET LOCAL lock_timeout='5s';
ALTER TABLE momentum_opportunities ADD COLUMN application_stage text NOT NULL DEFAULT 'saved'
 CHECK(application_stage IN ('saved','preparing','applied','interviewing','offered','accepted','rejected','withdrawn'));
CREATE INDEX momentum_opportunities_stage_idx ON momentum_opportunities(owner_id,application_stage,application_deadline);
COMMIT;

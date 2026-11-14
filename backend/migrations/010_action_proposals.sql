BEGIN;
SET LOCAL lock_timeout='5s';
CREATE TABLE momentum_actions (
 id uuid PRIMARY KEY, owner_id text NOT NULL CHECK(owner_id<>''), proposal jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','applied','rejected')),
 result_id uuid, created_at timestamptz NOT NULL DEFAULT now(), applied_at timestamptz
);
CREATE INDEX momentum_actions_owner_idx ON momentum_actions(owner_id,created_at DESC);
ALTER TABLE momentum_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE momentum_actions FORCE ROW LEVEL SECURITY;
REVOKE ALL ON momentum_actions FROM PUBLIC;
CREATE POLICY owner_only ON momentum_actions USING(owner_id=NULLIF(current_setting('momentum.user_id',true),'')) WITH CHECK(owner_id=NULLIF(current_setting('momentum.user_id',true),''));
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_actions TO momentum_app;
COMMIT;

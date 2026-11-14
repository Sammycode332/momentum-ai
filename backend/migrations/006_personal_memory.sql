BEGIN;
SET LOCAL lock_timeout = '5s';
CREATE TABLE momentum_preferences (
 owner_id text PRIMARY KEY CHECK(owner_id <> ''), personalization boolean NOT NULL DEFAULT true
);
CREATE TABLE momentum_memories (
 id uuid PRIMARY KEY, owner_id text NOT NULL CHECK(owner_id <> ''),
 content text NOT NULL CHECK(char_length(btrim(content)) BETWEEN 1 AND 500),
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX momentum_memories_owner_idx ON momentum_memories(owner_id,status,updated_at DESC);
CREATE TABLE momentum_audit (
 id uuid PRIMARY KEY, owner_id text NOT NULL CHECK(owner_id <> ''),
 event text NOT NULL, target_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX momentum_audit_owner_idx ON momentum_audit(owner_id,created_at DESC);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['momentum_preferences','momentum_memories','momentum_audit'] LOOP
 EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON %I FROM PUBLIC',t);
 EXECUTE format('CREATE POLICY owner_only ON %I USING(owner_id = NULLIF(current_setting(''momentum.user_id'',true),'''')) WITH CHECK(owner_id = NULLIF(current_setting(''momentum.user_id'',true),''''))',t);
 END LOOP;
END $$;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_preferences,momentum_memories TO momentum_app;
GRANT SELECT,INSERT ON momentum_audit TO momentum_app;
COMMIT;

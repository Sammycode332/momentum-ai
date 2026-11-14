BEGIN;
SET LOCAL lock_timeout = '5s';
CREATE TABLE momentum_practice (
 id uuid PRIMARY KEY, owner_id text NOT NULL CHECK(owner_id<>''),
 kind text NOT NULL CHECK(kind IN ('tutor','interview')), topic text NOT NULL,
 level text NOT NULL, format text NOT NULL, curriculum jsonb NOT NULL,
 step integer NOT NULL DEFAULT 0 CHECK(step>=0), packet jsonb NOT NULL,
 version integer NOT NULL DEFAULT 0, created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(id,owner_id)
);
CREATE TABLE momentum_practice_answers (
 id uuid PRIMARY KEY, owner_id text NOT NULL, session_id uuid NOT NULL,
 version integer NOT NULL, answer text NOT NULL CHECK(char_length(answer) BETWEEN 1 AND 4000),
 result jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(session_id,version), FOREIGN KEY(session_id,owner_id) REFERENCES momentum_practice(id,owner_id) ON DELETE CASCADE
);
CREATE INDEX momentum_practice_owner_idx ON momentum_practice(owner_id,updated_at DESC);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['momentum_practice','momentum_practice_answers'] LOOP
 EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON %I FROM PUBLIC',t);
 EXECUTE format('CREATE POLICY owner_only ON %I USING(owner_id = NULLIF(current_setting(''momentum.user_id'',true),'''')) WITH CHECK(owner_id = NULLIF(current_setting(''momentum.user_id'',true),''''))',t);
 END LOOP;
END $$;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_practice TO momentum_app;
GRANT SELECT,INSERT ON momentum_practice_answers TO momentum_app;
COMMIT;

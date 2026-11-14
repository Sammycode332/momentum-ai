BEGIN;
SET LOCAL lock_timeout = '5s';
-- Run as the schema/migration owner with CREATEROLE, never momentum_app.
-- This group cannot log in. Grant a separate worker login membership at activation.
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='momentum_scheduler') THEN
  CREATE ROLE momentum_scheduler NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
 END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='momentum_scheduler'
            AND (rolcanlogin OR rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication)) THEN
  RAISE EXCEPTION 'momentum_scheduler must be a restricted NOLOGIN group role; review existing role configuration';
 END IF;
 IF pg_has_role('momentum_app','momentum_scheduler','member') THEN
  RAISE EXCEPTION 'momentum_app must not be a scheduler member';
 END IF;
END $$;
ALTER TABLE momentum_preferences ADD COLUMN timezone text NOT NULL DEFAULT 'UTC',
 ADD COLUMN notifications_enabled boolean NOT NULL DEFAULT true,
 ADD COLUMN quiet_start integer NOT NULL DEFAULT 1320 CHECK(quiet_start BETWEEN 0 AND 1439),
 ADD COLUMN quiet_end integer NOT NULL DEFAULT 420 CHECK(quiet_end BETWEEN 0 AND 1439);
CREATE TABLE momentum_reminders (
 id uuid PRIMARY KEY, owner_id text NOT NULL CHECK(owner_id<>''),
 title text NOT NULL CHECK(char_length(btrim(title)) BETWEEN 1 AND 200),
 due_at timestamptz NOT NULL, timezone text NOT NULL,
 repeat text NOT NULL CHECK(repeat IN ('none','daily')),
 status text NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled','delivered','cancelled')),
 occurrence integer NOT NULL DEFAULT 0,
 next_check timestamptz NOT NULL DEFAULT now(),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(id,owner_id)
);
CREATE INDEX momentum_reminders_due_idx ON momentum_reminders(due_at) WHERE status='scheduled';
CREATE INDEX momentum_reminders_owner_idx ON momentum_reminders(owner_id,due_at);
CREATE TABLE momentum_notifications (
 id uuid PRIMARY KEY, owner_id text NOT NULL, reminder_id uuid NOT NULL,
 occurrence integer NOT NULL, title text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 state text NOT NULL DEFAULT 'unread' CHECK(state IN ('unread','read','dismissed')),
 snoozed boolean NOT NULL DEFAULT false,
 UNIQUE(reminder_id,occurrence), FOREIGN KEY(reminder_id,owner_id) REFERENCES momentum_reminders(id,owner_id) ON DELETE CASCADE
);
CREATE INDEX momentum_notifications_owner_idx ON momentum_notifications(owner_id,created_at DESC);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['momentum_reminders','momentum_notifications'] LOOP
 EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON %I FROM PUBLIC',t);
 EXECUTE format('CREATE POLICY owner_only ON %I TO momentum_app USING(owner_id = NULLIF(current_setting(''momentum.user_id'',true),'''')) WITH CHECK(owner_id = NULLIF(current_setting(''momentum.user_id'',true),''''))',t);
 EXECUTE format('CREATE POLICY scheduler_access ON %I TO momentum_scheduler USING(true) WITH CHECK(true)',t);
 END LOOP;
END $$;
CREATE POLICY scheduler_preferences ON momentum_preferences FOR SELECT TO momentum_scheduler USING(true);
GRANT USAGE ON SCHEMA public TO momentum_scheduler;
GRANT SELECT,UPDATE ON momentum_reminders TO momentum_scheduler;
GRANT SELECT,INSERT ON momentum_notifications TO momentum_scheduler;
GRANT SELECT ON momentum_preferences TO momentum_scheduler;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_reminders,momentum_notifications TO momentum_app;
COMMIT;

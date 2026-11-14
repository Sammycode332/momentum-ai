BEGIN;
SET LOCAL lock_timeout='5s';
CREATE TABLE momentum_source_cache (source text PRIMARY KEY,payload jsonb NOT NULL DEFAULT '[]',fetched_at timestamptz,next_fetch timestamptz NOT NULL DEFAULT now());
INSERT INTO momentum_source_cache(source) VALUES ('remotive');
REVOKE ALL ON momentum_source_cache FROM PUBLIC;
GRANT SELECT,UPDATE ON momentum_source_cache TO momentum_app;
CREATE TABLE momentum_ai_usage(owner_id text NOT NULL,window_start timestamptz NOT NULL,period text NOT NULL,count integer NOT NULL,PRIMARY KEY(owner_id,window_start,period));
ALTER TABLE momentum_ai_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE momentum_ai_usage FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_only ON momentum_ai_usage USING(owner_id=NULLIF(current_setting('momentum.user_id',true),'')) WITH CHECK(owner_id=NULLIF(current_setting('momentum.user_id',true),''));
REVOKE ALL ON momentum_ai_usage FROM PUBLIC;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_ai_usage TO momentum_app;
CREATE TABLE momentum_push_subscriptions (
 id uuid PRIMARY KEY,owner_id text NOT NULL,endpoint text NOT NULL UNIQUE,
 p256dh text NOT NULL,auth text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(id,owner_id)
);
CREATE TABLE momentum_push_deliveries (
 notification_id uuid NOT NULL REFERENCES momentum_notifications(id) ON DELETE CASCADE,
 subscription_id uuid NOT NULL REFERENCES momentum_push_subscriptions(id) ON DELETE CASCADE,
 owner_id text NOT NULL,attempts integer NOT NULL DEFAULT 0,
 next_attempt timestamptz NOT NULL DEFAULT now(),status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','failed')),
 PRIMARY KEY(notification_id,subscription_id)
);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['momentum_push_subscriptions','momentum_push_deliveries'] LOOP
 EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
 EXECUTE format('REVOKE ALL ON %I FROM PUBLIC',t);
 EXECUTE format('CREATE POLICY owner_only ON %I TO momentum_app USING(owner_id = NULLIF(current_setting(''momentum.user_id'',true),'''')) WITH CHECK(owner_id = NULLIF(current_setting(''momentum.user_id'',true),''''))',t);
 EXECUTE format('CREATE POLICY scheduler_access ON %I TO momentum_scheduler USING(true) WITH CHECK(true)',t);
 END LOOP;
END $$;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_push_subscriptions TO momentum_app;
GRANT SELECT ON momentum_push_deliveries TO momentum_app;
GRANT SELECT,DELETE ON momentum_push_subscriptions TO momentum_scheduler;
GRANT SELECT,INSERT,UPDATE,DELETE ON momentum_push_deliveries TO momentum_scheduler;
COMMIT;

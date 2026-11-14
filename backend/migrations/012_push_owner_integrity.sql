BEGIN;
SET LOCAL lock_timeout='5s';
ALTER TABLE momentum_notifications ADD CONSTRAINT notifications_id_owner_unique UNIQUE(id,owner_id);
ALTER TABLE momentum_push_deliveries ADD CONSTRAINT push_notification_owner_fk
 FOREIGN KEY(notification_id,owner_id) REFERENCES momentum_notifications(id,owner_id) ON DELETE CASCADE;
ALTER TABLE momentum_push_deliveries ADD CONSTRAINT push_subscription_owner_fk
 FOREIGN KEY(subscription_id,owner_id) REFERENCES momentum_push_subscriptions(id,owner_id) ON DELETE CASCADE;
CREATE INDEX momentum_push_pending_idx ON momentum_push_deliveries(next_attempt) WHERE status='pending';
CREATE INDEX momentum_push_owner_idx ON momentum_push_subscriptions(owner_id);
COMMIT;

BEGIN;
SET LOCAL lock_timeout = '5s';

ALTER TABLE public.momentum_goals
    ADD COLUMN completed boolean NOT NULL DEFAULT false;

CREATE POLICY goals_update_own ON public.momentum_goals FOR UPDATE
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''))
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));
CREATE POLICY goals_delete_own ON public.momentum_goals FOR DELETE
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));

GRANT UPDATE (title, completed), DELETE ON public.momentum_goals TO momentum_app;

COMMIT;

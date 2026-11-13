BEGIN;

CREATE TABLE public.momentum_onboarding (
    owner_id text PRIMARY KEY CHECK (owner_id <> ''),
    status text NOT NULL CHECK (status IN ('completed', 'skipped')),
    primary_focus text,
    current_goals text,
    planning_time text,
    CONSTRAINT onboarding_fields_match_status CHECK (
        (status = 'skipped' AND primary_focus IS NULL
            AND current_goals IS NULL AND planning_time IS NULL)
        OR
        (status = 'completed' AND primary_focus IS NOT NULL
            AND char_length(btrim(primary_focus)) BETWEEN 1 AND 120
            AND current_goals IS NOT NULL
            AND char_length(btrim(current_goals)) BETWEEN 1 AND 1000
            AND planning_time IS NOT NULL
            AND planning_time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$')
    )
);

REVOKE ALL ON public.momentum_onboarding FROM PUBLIC;
ALTER TABLE public.momentum_onboarding ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.momentum_onboarding FORCE ROW LEVEL SECURITY;

CREATE POLICY onboarding_select_own ON public.momentum_onboarding FOR SELECT
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));
CREATE POLICY onboarding_insert_own ON public.momentum_onboarding FOR INSERT
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));
CREATE POLICY onboarding_update_own ON public.momentum_onboarding FOR UPDATE
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''))
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));

COMMIT;

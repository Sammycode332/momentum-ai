BEGIN;

CREATE TABLE public.momentum_goals (
    id uuid PRIMARY KEY,
    owner_id text NOT NULL CHECK (owner_id <> ''),
    title text NOT NULL CHECK (char_length(btrim(title)) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX momentum_goals_owner_created_idx
    ON public.momentum_goals (owner_id, created_at DESC, id DESC);

REVOKE ALL ON public.momentum_goals FROM PUBLIC;
ALTER TABLE public.momentum_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.momentum_goals FORCE ROW LEVEL SECURITY;

CREATE POLICY goals_select_own ON public.momentum_goals FOR SELECT
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));
CREATE POLICY goals_insert_own ON public.momentum_goals FOR INSERT
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));

COMMIT;

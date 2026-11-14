BEGIN;

CREATE TABLE public.momentum_projects (
    id uuid PRIMARY KEY, owner_id text NOT NULL CHECK (owner_id <> ''),
    name text NOT NULL CHECK (char_length(btrim(name)) BETWEEN 1 AND 200),
    description text, status text NOT NULL CHECK (status IN ('not_started','in_progress','completed','paused')),
    deadline date, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, owner_id)
);
CREATE TABLE public.momentum_tasks (
    id uuid PRIMARY KEY, owner_id text NOT NULL CHECK (owner_id <> ''),
    title text NOT NULL CHECK (char_length(btrim(title)) BETWEEN 1 AND 200), description text,
    status text NOT NULL CHECK (status IN ('not_started','in_progress','completed','paused')),
    priority text NOT NULL CHECK (priority IN ('low','medium','high')), due_date date, project_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (project_id, owner_id) REFERENCES public.momentum_projects (id, owner_id) ON DELETE SET NULL (project_id)
);
CREATE TABLE public.momentum_learning (
    id uuid PRIMARY KEY, owner_id text NOT NULL CHECK (owner_id <> ''),
    subject text NOT NULL CHECK (char_length(btrim(subject)) BETWEEN 1 AND 200),
    objective text NOT NULL CHECK (char_length(btrim(objective)) BETWEEN 1 AND 2000),
    progress_status text NOT NULL CHECK (progress_status IN ('not_started','in_progress','completed','paused')),
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.momentum_academics (
    id uuid PRIMARY KEY, owner_id text NOT NULL CHECK (owner_id <> ''),
    activity text NOT NULL CHECK (char_length(btrim(activity)) BETWEEN 1 AND 200), description text,
    status text NOT NULL CHECK (status IN ('not_started','in_progress','completed','paused')), deadline date,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.momentum_opportunities (
    id uuid PRIMARY KEY, owner_id text NOT NULL CHECK (owner_id <> ''),
    name text NOT NULL CHECK (char_length(btrim(name)) BETWEEN 1 AND 200),
    type text NOT NULL CHECK (char_length(btrim(type)) BETWEEN 1 AND 200),
    status text NOT NULL CHECK (status IN ('not_started','in_progress','completed','paused')),
    application_deadline date, url text CHECK (url IS NULL OR url ~ '^https?://'),
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX momentum_projects_owner_updated_idx ON public.momentum_projects (owner_id, updated_at DESC);
CREATE INDEX momentum_tasks_owner_updated_idx ON public.momentum_tasks (owner_id, updated_at DESC);
CREATE INDEX momentum_tasks_project_idx ON public.momentum_tasks (project_id);
CREATE INDEX momentum_learning_owner_updated_idx ON public.momentum_learning (owner_id, updated_at DESC);
CREATE INDEX momentum_academics_owner_updated_idx ON public.momentum_academics (owner_id, updated_at DESC);
CREATE INDEX momentum_opportunities_owner_updated_idx ON public.momentum_opportunities (owner_id, updated_at DESC);

REVOKE ALL ON public.momentum_projects, public.momentum_tasks, public.momentum_learning, public.momentum_academics, public.momentum_opportunities FROM PUBLIC;

DO $$ DECLARE table_name text; BEGIN
  FOREACH table_name IN ARRAY ARRAY['momentum_projects','momentum_tasks','momentum_learning','momentum_academics','momentum_opportunities'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', table_name);
    EXECUTE format('CREATE POLICY %I ON public.%I FOR SELECT USING (owner_id = NULLIF(current_setting(''momentum.user_id'', true), ''''))', table_name || '_select_own', table_name);
    EXECUTE format('CREATE POLICY %I ON public.%I FOR INSERT WITH CHECK (owner_id = NULLIF(current_setting(''momentum.user_id'', true), ''''))', table_name || '_insert_own', table_name);
    EXECUTE format('CREATE POLICY %I ON public.%I FOR UPDATE USING (owner_id = NULLIF(current_setting(''momentum.user_id'', true), '''')) WITH CHECK (owner_id = NULLIF(current_setting(''momentum.user_id'', true), ''''))', table_name || '_update_own', table_name);
    EXECUTE format('CREATE POLICY %I ON public.%I FOR DELETE USING (owner_id = NULLIF(current_setting(''momentum.user_id'', true), ''''))', table_name || '_delete_own', table_name);
  END LOOP;
END $$;
COMMIT;

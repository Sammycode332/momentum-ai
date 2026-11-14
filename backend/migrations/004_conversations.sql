BEGIN;

CREATE TABLE public.momentum_conversations (
    id uuid PRIMARY KEY,
    owner_id text NOT NULL CHECK (owner_id <> ''),
    title text NOT NULL CHECK (char_length(btrim(title)) BETWEEN 1 AND 120),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, owner_id)
);

CREATE TABLE public.momentum_conversation_messages (
    conversation_id uuid NOT NULL,
    owner_id text NOT NULL,
    turn_id uuid NOT NULL,
    position integer NOT NULL CHECK (position > 0),
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL CHECK (char_length(btrim(content)) BETWEEN 1 AND 4000),
    PRIMARY KEY (conversation_id, turn_id, role),
    UNIQUE (conversation_id, position, role),
    FOREIGN KEY (conversation_id, owner_id)
        REFERENCES public.momentum_conversations (id, owner_id) ON DELETE CASCADE
);

CREATE INDEX momentum_conversations_recent
    ON public.momentum_conversations (owner_id, updated_at DESC, id DESC);

ALTER TABLE public.momentum_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.momentum_conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE public.momentum_conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.momentum_conversation_messages FORCE ROW LEVEL SECURITY;
REVOKE ALL ON public.momentum_conversations, public.momentum_conversation_messages FROM PUBLIC;

CREATE POLICY conversation_owner ON public.momentum_conversations
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''))
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));
CREATE POLICY conversation_message_owner ON public.momentum_conversation_messages
    USING (owner_id = NULLIF(current_setting('momentum.user_id', true), ''))
    WITH CHECK (owner_id = NULLIF(current_setting('momentum.user_id', true), ''));

COMMIT;

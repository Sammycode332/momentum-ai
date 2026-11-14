BEGIN;
SET LOCAL lock_timeout = '5s';
ALTER TABLE momentum_goals ADD CONSTRAINT momentum_goals_id_owner UNIQUE(id,owner_id);
ALTER TABLE momentum_tasks ADD CONSTRAINT momentum_tasks_id_owner UNIQUE(id,owner_id);
ALTER TABLE momentum_tasks ADD COLUMN goal_id uuid,
 ADD COLUMN parent_id uuid,
 ADD COLUMN kind text NOT NULL DEFAULT 'task' CHECK(kind IN ('task','milestone')),
 ADD CONSTRAINT task_goal_owner FOREIGN KEY(goal_id,owner_id) REFERENCES momentum_goals(id,owner_id) ON DELETE SET NULL(goal_id),
 ADD CONSTRAINT task_parent_owner FOREIGN KEY(parent_id,owner_id) REFERENCES momentum_tasks(id,owner_id) ON DELETE SET NULL(parent_id),
 ADD CONSTRAINT task_not_own_parent CHECK(parent_id IS NULL OR parent_id<>id);
CREATE INDEX momentum_tasks_goal_idx ON momentum_tasks(goal_id);
CREATE INDEX momentum_tasks_parent_idx ON momentum_tasks(parent_id);
COMMIT;

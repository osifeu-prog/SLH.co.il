BEGIN;

UPDATE user_tasks
SET completed = FALSE
WHERE completed IS NULL;

ALTER TABLE user_tasks
  ALTER COLUMN user_id SET NOT NULL,
  ALTER COLUMN task_id SET NOT NULL,
  ALTER COLUMN completed SET NOT NULL,
  ALTER COLUMN completed SET DEFAULT FALSE;

ALTER TABLE user_tasks
  ADD CONSTRAINT user_tasks_pkey PRIMARY KEY (user_id, task_id);

COMMIT;
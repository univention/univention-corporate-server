-- Update script to update nag 1.1 data to 2.x data for pgsql
-- Converted from mysql version by Daniel E. Markle <lexicon@seul.org>
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ psql <db name> -f < 1.1_to_2.0.pgsql.sql

ALTER TABLE nag_tasks DROP COLUMN task_modified;

BEGIN;
ALTER TABLE nag_tasks ADD COLUMN task_category_new VARCHAR(80);
UPDATE nag_tasks SET task_category_new = task_category;
ALTER TABLE nag_tasks DROP task_category;
ALTER TABLE nag_tasks RENAME task_category_new TO task_category;
COMMIT;

BEGIN;
ALTER TABLE nag_tasks ADD COLUMN task_id_new VARCHAR(32);
UPDATE nag_tasks SET task_id_new = task_id;
ALTER TABLE nag_tasks DROP task_id;
ALTER TABLE nag_tasks RENAME task_id_new TO task_id;
ALTER TABLE nag_tasks ALTER COLUMN task_id SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE nag_tasks ADD COLUMN task_private_new SMALLINT;
UPDATE nag_tasks SET task_private_new = task_private;
ALTER TABLE nag_tasks DROP task_private;
ALTER TABLE nag_tasks RENAME task_private_new TO task_private;
ALTER TABLE nag_tasks ALTER COLUMN task_private SET NOT NULL;
ALTER TABLE nag_tasks ALTER COLUMN task_private SET DEFAULT 0;
COMMIT;

BEGIN;
ALTER TABLE nag_tasks ADD COLUMN task_uid VARCHAR(255);
UPDATE nag_tasks SET task_uid = '';
ALTER TABLE nag_tasks ALTER COLUMN task_uid SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE nag_tasks ADD COLUMN task_alarm INT;
UPDATE nag_tasks SET task_alarm = 0;
ALTER TABLE nag_tasks ALTER COLUMN task_alarm SET NOT NULL;
COMMIT;

ALTER TABLE nag_tasks ADD INDEX nag_tasklist_idx (task_owner);
ALTER TABLE nag_tasks ADD INDEX nag_uid_idx (task_uid);

UPDATE nag_tasks SET task_id = task_owner || task_id;
UPDATE nag_tasks SET task_uid = 'nag:' || task_id WHERE task_id NOT LIKE 'nag:%';

-- this assumes the default constraint name was used at table creation time
ALTER TABLE nag_tasks DROP CONSTRAINT nag_tasks_pkey;
ALTER TABLE nag_tasks ADD CONSTRAINT nag_tasks_pkey PRIMARY KEY (task_id);

CREATE INDEX nag_uid_idx ON nag_tasks (task_uid);

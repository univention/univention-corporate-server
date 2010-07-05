-- $Horde: nag/scripts/upgrades/1.1_to_2.0.oci8.sql,v 1.1.2.3 2009-10-19 10:54:37 jan Exp $

ALTER TABLE nag_tasks DROP COLUMN task_modified;

ALTER TABLE nag_tasks ADD task_category_new VARCHAR2(80);
UPDATE nag_tasks SET task_category_new = task_category;
ALTER TABLE nag_tasks DROP COLUMN task_category;
ALTER TABLE nag_tasks RENAME COLUMN task_category_new TO task_category;

ALTER TABLE nag_tasks MODIFY task_name VARCHAR2(255);
ALTER TABLE nag_tasks MODIFY task_private NUMBER(16) DEFAULT 0;

ALTER TABLE nag_tasks ADD task_uid VARCHAR2(255);
ALTER TABLE nag_tasks ADD task_alarm NUMBER(16) DEFAULT 0 NOT NULL;

CREATE INDEX nag_tasklist_idx ON nag_tasks (task_owner);
CREATE INDEX nag_uid_idx ON nag_tasks (task_uid);

ALTER TABLE nag_tasks ADD task_id_new VARCHAR2(32);
UPDATE nag_tasks SET task_id_new = task_id;
ALTER TABLE nag_tasks ADD task_owner_new VARCHAR2(255);
UPDATE nag_tasks SET task_owner_new = task_owner;
ALTER TABLE nag_tasks DROP (task_id, task_owner);
ALTER TABLE nag_tasks RENAME COLUMN task_id_new to task_id;
ALTER TABLE nag_tasks RENAME COLUMN task_owner_new to task_owner;

UPDATE nag_tasks SET task_id = CONCAT(task_owner, task_id);
UPDATE nag_tasks SET task_uid = CONCAT('nag:', task_id) WHERE task_id NOT LIKE 'nag:%';

ALTER TABLE nag_tasks ADD CONSTRAINT task_id PRIMARY KEY (task_id);

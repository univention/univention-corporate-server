-- $Horde: nag/scripts/upgrades/1.1_to_2.0.mysql.sql,v 1.6.2.3 2007-12-20 14:23:38 jan Exp $
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 1.1_to_2.0.mysql.sql

ALTER TABLE nag_tasks DROP COLUMN task_modified;

ALTER TABLE nag_tasks CHANGE COLUMN task_category task_category VARCHAR(80);
ALTER TABLE nag_tasks CHANGE COLUMN task_id task_id VARCHAR(32) NOT NULL;
ALTER TABLE nag_tasks CHANGE COLUMN task_private task_private SMALLINT DEFAULT 0 NOT NULL;

ALTER TABLE nag_tasks ADD COLUMN task_uid VARCHAR(255) NOT NULL;
ALTER TABLE nag_tasks ADD COLUMN task_alarm INT NOT NULL;

ALTER TABLE nag_tasks ADD INDEX nag_tasklist_idx (task_owner);
ALTER TABLE nag_tasks ADD INDEX nag_uid_idx (task_uid);

UPDATE nag_tasks SET task_id = CONCAT(task_owner, task_id);
UPDATE nag_tasks SET task_uid = CONCAT('nag:', task_id) WHERE task_id NOT LIKE 'nag:%';

ALTER TABLE nag_tasks DROP PRIMARY KEY;
ALTER TABLE nag_tasks ADD PRIMARY KEY (task_id);

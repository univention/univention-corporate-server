-- $Horde: mnemo/scripts/upgrades/1.1_to_2.0.mysql.sql,v 1.4.2.1 2009-10-20 21:44:35 jan Exp $
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 1.1_to_2.0.mysql.sql

ALTER TABLE mnemo_memos DROP COLUMN memo_modified;

ALTER TABLE mnemo_memos ADD COLUMN memo_uid VARCHAR(255) NOT NULL;

ALTER TABLE mnemo_memos CHANGE COLUMN memo_id memo_id VARCHAR(32) NOT NULL;
ALTER TABLE mnemo_memos CHANGE COLUMN memo_category memo_category VARCHAR(80);
ALTER TABLE mnemo_memos CHANGE COLUMN memo_private memo_private SMALLINT DEFAULT 0 NOT NULL;

CREATE INDEX mnemo_uid_idx ON mnemo_memos (memo_uid);

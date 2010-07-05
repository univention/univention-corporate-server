-- Update script to update mnemo 1.1 data to 2.x data for pgsql
-- Converted from mysql version by Daniel E. Markle <lexicon@seul.org>
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ psql <db name> -f < 1.1_to_2.0.pgsql.sql

ALTER TABLE mnemo_memos DROP COLUMN memo_modified;

BEGIN;
ALTER TABLE mnemo_memos ADD COLUMN memo_uid VARCHAR(255);
UPDATE mnemo_memos SET memo_uid = '';
ALTER TABLE mnemo_memos ALTER COLUMN memo_uid SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE mnemo_memos ADD COLUMN memo_id_new VARCHAR(32);
UPDATE mnemo_memos SET memo_id_new = memo_id;
ALTER TABLE mnemo_memos DROP memo_id;
ALTER TABLE mnemo_memos RENAME memo_id_new TO memo_id;
ALTER TABLE mnemo_memos ALTER COLUMN memo_id SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE mnemo_memos ADD COLUMN memo_category_new VARCHAR(80);
UPDATE mnemo_memos SET memo_category_new = memo_category;
ALTER TABLE mnemo_memos DROP memo_category;
ALTER TABLE mnemo_memos RENAME memo_category_new TO memo_category;
COMMIT;

BEGIN;
ALTER TABLE mnemo_memos ADD COLUMN memo_private_new SMALLINT;
UPDATE mnemo_memos SET memo_private_new = memo_private;
ALTER TABLE mnemo_memos DROP memo_private;
ALTER TABLE mnemo_memos RENAME memo_private_new TO memo_private;
ALTER TABLE mnemo_memos ALTER COLUMN memo_private SET NOT NULL;
ALTER TABLE mnemo_memos ALTER COLUMN memo_private SET DEFAULT 0;
COMMIT;

CREATE INDEX mnemo_uid_idx ON mnemo_memos (memo_uid);

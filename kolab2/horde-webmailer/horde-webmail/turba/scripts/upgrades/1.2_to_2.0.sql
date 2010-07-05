-- You can simply execute this file in your database.
--
-- For MySQL run:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 1.2_to_2.0.sql
--
-- Or, for PostgreSQL:
--
-- $ psql <db name> -f 1.2_to_2.0.sql


ALTER TABLE turba_objects ADD COLUMN object_uid VARCHAR(255);
ALTER TABLE turba_objects ADD COLUMN object_freebusyurl VARCHAR(255);
ALTER TABLE turba_objects ADD COLUMN object_smimepublickey TEXT;
ALTER TABLE turba_objects ADD COLUMN object_pgppublickey TEXT;

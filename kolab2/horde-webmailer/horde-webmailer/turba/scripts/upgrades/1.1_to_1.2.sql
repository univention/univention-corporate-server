-- You can simply execute this file in your database.
--
-- For MySQL run:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 1.1_to_1.2.sql
--
-- Or, for PostgreSQL:
--
-- $ psql <db name> -f 1.1_to_1.2.sql

ALTER TABLE turba_objects CHANGE object_homeAddress object_homeaddress VARCHAR(255);
ALTER TABLE turba_objects CHANGE object_workAddress object_workaddress VARCHAR(255);
ALTER TABLE turba_objects CHANGE object_homePhone object_homephone VARCHAR(25);
ALTER TABLE turba_objects CHANGE object_workPhone object_workphone VARCHAR(25);
ALTER TABLE turba_objects CHANGE object_cellPhone object_cellphone VARCHAR(25);
ALTER TABLE turba_objects MODIFY object_title VARCHAR(255);
ALTER TABLE turba_objects MODIFY object_company VARCHAR(255);
ALTER TABLE turba_objects ADD object_type VARCHAR(255) DEFAULT 'Object' NOT NULL;
ALTER TABLE turba_objects ADD object_members BLOB;
CREATE INDEX turba_owner_idx ON turba_objects (owner_id);


-- $Horde: turba/scripts/sql/turba_objects.pgsql.sql,v 1.9 2007/06/25 06:56:50 slusarz Exp $
-- You can simply execute this file in your database.
-- 
-- Run as:
--
-- $ psql -d DATABASE_NAME < turba_objects.pgsql.sql

CREATE TABLE turba_objects (
    object_id VARCHAR(32) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    object_type VARCHAR(255) DEFAULT 'Object' NOT NULL,
    object_uid VARCHAR(255),
    object_members TEXT,
    object_lastname VARCHAR(255) DEFAULT '' NOT NULL,
    object_firstname VARCHAR(255),
    object_alias VARCHAR(32),
    object_nameprefix VARCHAR(255),
    object_email VARCHAR(255),
    object_homestreet VARCHAR(255),
    object_homecity VARCHAR(255),
    object_homeprovince VARCHAR(255),
    object_homepostalcode VARCHAR(255),
    object_homecountry VARCHAR(255),
    object_workstreet VARCHAR(255),
    object_workcity VARCHAR(255),
    object_workprovince VARCHAR(255),
    object_workpostalcode VARCHAR(255),
    object_workcountry VARCHAR(255),
    object_homephone VARCHAR(25),
    object_workphone VARCHAR(25),
    object_cellphone VARCHAR(25),
    object_fax VARCHAR(25),
    object_pager VARCHAR(25),
    object_title VARCHAR(255),
    object_company VARCHAR(255),
    object_notes TEXT,
    object_url VARCHAR(255),
    object_pgppublickey TEXT,
    object_smimepublickey TEXT,
    object_freebusyurl VARCHAR(255),
    object_role VARCHAR(255),
    object_category VARCHAR(80),
    object_photo TEXT,
    object_blobtype VARCHAR(10),
    object_bday VARCHAR(10),

    PRIMARY KEY(object_id)
);

ALTER TABLE turba_objects OWNER TO horde;

CREATE INDEX turba_owner_idx ON turba_objects (owner_id);

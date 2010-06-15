-- $Horde: turba/scripts/drivers/oci8_create.sql,v 1.2 2003/02/18 05:12:44 chuck Exp $

CREATE TABLE turba_objects (
    object_id VARCHAR2(32) NOT NULL,
    owner_id VARCHAR2(255) NOT NULL,
    object_type VARCHAR2(255) NOT NULL DEFAULT 'Object',
    object_members CLOB,
    object_name VARCHAR2(255),
    object_alias VARCHAR2(32),
    object_email VARCHAR2(255),
    object_homeaddress VARCHAR2(255),
    object_workaddress VARCHAR2(255),
    object_homephone VARCHAR2(25),
    object_workphone VARCHAR2(25),
    object_cellphone VARCHAR2(25),
    object_fax VARCHAR2(25),
    object_title VARCHAR2(255),
    object_company VARCHAR2(255),
    object_notes CLOB,
    object_pgppublickey CLOB,
    object_smimepublickey CLOB,
    object_freebusyurl VARCHAR2(255),
    
    PRIMARY KEY(object_id)
);

CREATE INDEX turba_owner_idx ON turba_objects (owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON turba_objects TO horde;

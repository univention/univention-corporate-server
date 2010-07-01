-- $Horde: turba/scripts/sql/turba.oci8.sql,v 1.1.2.11 2009-10-20 21:44:34 jan Exp $

CREATE TABLE turba_objects (
    object_id VARCHAR2(32) NOT NULL,
    owner_id VARCHAR2(255) NOT NULL,
    object_type VARCHAR2(255) DEFAULT 'Object' NOT NULL,
    object_uid VARCHAR2(255),
    object_members CLOB,
    object_firstname VARCHAR2(255),
    object_lastname VARCHAR2(255),
    object_middlenames VARCHAR2(255),
    object_nameprefix VARCHAR2(32),
    object_namesuffix VARCHAR2(32),
    object_alias VARCHAR2(32),
    object_photo BLOB,
    object_phototype VARCHAR2(10),
    object_bday VARCHAR2(10),
    object_homestreet VARCHAR2(255),
    object_homepob VARCHAR2(10),
    object_homecity VARCHAR2(255),
    object_homeprovince VARCHAR2(255),
    object_homepostalcode VARCHAR2(10),
    object_homecountry VARCHAR2(255),
    object_workstreet VARCHAR2(255),
    object_workpob VARCHAR2(10),
    object_workcity VARCHAR2(255),
    object_workprovince VARCHAR2(255),
    object_workpostalcode VARCHAR2(10),
    object_workcountry VARCHAR2(255),
    object_tz VARCHAR2(32),
    object_geo VARCHAR2(255),
    object_email VARCHAR2(255),
    object_homephone VARCHAR2(25),
    object_workphone VARCHAR2(25),
    object_cellphone VARCHAR2(25),
    object_fax VARCHAR2(25),
    object_pager VARCHAR2(25),
    object_title VARCHAR2(255),
    object_role VARCHAR2(255),
    object_logo BLOB,
    object_logotype VARCHAR2(10),
    object_company VARCHAR2(255),
    object_category VARCHAR2(80),
    object_notes CLOB,
    object_url VARCHAR2(255),
    object_freebusyurl VARCHAR2(255),
    object_pgppublickey CLOB,
    object_smimepublickey CLOB,
    PRIMARY KEY(object_id)
);

CREATE INDEX turba_owner_idx ON turba_objects (owner_id);
CREATE INDEX turba_email_idx ON turba_objects (object_email);
CREATE INDEX turba_firstname_idx ON turba_objects (object_firstname);
CREATE INDEX turba_lastname_idx ON turba_objects (object_lastname);

CREATE TABLE turba_shares (
    share_id NUMBER(16) NOT NULL,
    share_name VARCHAR2(255) NOT NULL,
    share_owner VARCHAR2(255) NOT NULL,
    share_flags NUMBER(8) DEFAULT 0 NOT NULL,
    perm_creator NUMBER(8) DEFAULT 0 NOT NULL,
    perm_default NUMBER(8) DEFAULT 0 NOT NULL,
    perm_guest NUMBER(8) DEFAULT 0 NOT NULL,
    attribute_name VARCHAR2(255) NOT NULL,
    attribute_desc VARCHAR2(255),
    attribute_params VARCHAR2(4000),
    PRIMARY KEY (share_id)
);

CREATE INDEX turba_shares_name_idx ON turba_shares (share_name);
CREATE INDEX turba_shares_owner_idx ON turba_shares (share_owner);
CREATE INDEX turba_shares_creator_idx ON turba_shares (perm_creator);
CREATE INDEX turba_shares_default_idx ON turba_shares (perm_default);
CREATE INDEX turba_shares_guest_idx ON turba_shares (perm_guest);

CREATE TABLE turba_shares_groups (
    share_id NUMBER(16) NOT NULL,
    group_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX turba_groups_share_id_idx ON turba_shares_groups (share_id);
CREATE INDEX turba_groups_group_uid_idx ON turba_shares_groups (group_uid);
CREATE INDEX turba_groups_perm_idx ON turba_shares_groups (perm);

CREATE TABLE turba_shares_users (
    share_id NUMBER(16) NOT NULL,
    user_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX turba_users_share_id_idx ON turba_shares_users (share_id);
CREATE INDEX turba_users_user_uid_idx ON turba_shares_users (user_uid);
CREATE INDEX turba_users_perm_idx ON turba_shares_users (perm);

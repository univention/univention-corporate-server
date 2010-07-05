-- $Horde: turba/scripts/sql/turba.mssql.sql,v 1.1.2.10 2009-11-07 13:04:57 jan Exp $

CREATE TABLE turba_objects (
    object_id VARCHAR(32) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    object_type VARCHAR(255) DEFAULT 'Object' NOT NULL,
    object_uid VARCHAR(255),
    object_members IMAGE,
    object_firstname VARCHAR(255),
    object_lastname VARCHAR(255),
    object_middlenames VARCHAR(255),
    object_nameprefix VARCHAR(32),
    object_namesuffix VARCHAR(32),
    object_alias VARCHAR(32),
    object_photo IMAGE,
    object_phototype VARCHAR(10),
    object_bday VARCHAR(10),
    object_homestreet VARCHAR(255),
    object_homepob VARCHAR(10),
    object_homecity VARCHAR(255),
    object_homeprovince VARCHAR(255),
    object_homepostalcode VARCHAR(10),
    object_homecountry VARCHAR(255),
    object_workstreet VARCHAR(255),
    object_workpob VARCHAR(10),
    object_workcity VARCHAR(255),
    object_workprovince VARCHAR(255),
    object_workpostalcode VARCHAR(10),
    object_workcountry VARCHAR(255),
    object_tz VARCHAR(32),
    object_geo VARCHAR(255),
    object_email VARCHAR(255),
    object_homephone VARCHAR(25),
    object_workphone VARCHAR(25),
    object_cellphone VARCHAR(25),
    object_fax VARCHAR(25),
    object_pager VARCHAR(25),
    object_title VARCHAR(255),
    object_role VARCHAR(255),
    object_logo IMAGE,
    object_logotype VARCHAR(10),
    object_company VARCHAR(255),
    object_category VARCHAR(80),
    object_notes VARCHAR(MAX),
    object_url VARCHAR(255),
    object_freebusyurl VARCHAR(255),
    object_pgppublickey VARCHAR(MAX),
    object_smimepublickey VARCHAR(MAX),
--
    PRIMARY KEY(object_id)
);

CREATE INDEX turba_owner_idx ON turba_objects (owner_id);
CREATE INDEX turba_email_idx ON turba_objects (object_email);
CREATE INDEX turba_firstname_idx ON turba_objects (object_firstname);
CREATE INDEX turba_lastname_idx ON turba_objects (object_lastname);

CREATE TABLE turba_shares (
    share_id INT NOT NULL,
    share_name VARCHAR(255) NOT NULL,
    share_owner VARCHAR(255) NOT NULL,
    share_flags SMALLINT DEFAULT 0 NOT NULL,
    perm_creator SMALLINT DEFAULT 0 NOT NULL,
    perm_default SMALLINT DEFAULT 0 NOT NULL,
    perm_guest SMALLINT DEFAULT 0 NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_desc VARCHAR(255),
    attribute_params VARCHAR(MAX),
    PRIMARY KEY (share_id)
);

CREATE INDEX turba_shares_share_name_idx ON turba_shares (share_name);
CREATE INDEX turba_shares_share_owner_idx ON turba_shares (share_owner);
CREATE INDEX turba_shares_perm_creator_idx ON turba_shares (perm_creator);
CREATE INDEX turba_shares_perm_default_idx ON turba_shares (perm_default);
CREATE INDEX turba_shares_perm_guest_idx ON turba_shares (perm_guest);

CREATE TABLE turba_shares_groups (
    share_id INT NOT NULL,
    group_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX turba_shares_groups_share_id_idx ON turba_shares_groups (share_id);
CREATE INDEX turba_shares_groups_group_uid_idx ON turba_shares_groups (group_uid);
CREATE INDEX turba_shares_groups_perm_idx ON turba_shares_groups (perm);

CREATE TABLE turba_shares_users (
    share_id INT NOT NULL,
    user_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX turba_shares_users_share_id_idx ON turba_shares_users (share_id);
CREATE INDEX turba_shares_users_user_uid_idx ON turba_shares_users (user_uid);
CREATE INDEX turba_shares_users_perm_idx ON turba_shares_users (perm);

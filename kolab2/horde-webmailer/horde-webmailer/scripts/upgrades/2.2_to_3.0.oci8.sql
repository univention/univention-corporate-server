-- $Horde: horde/scripts/upgrades/2.2_to_3.0.oci8.sql,v 1.1.2.2 2007-12-20 15:03:04 jan Exp $

ALTER TABLE horde_prefs MODIFY pref_uid VARCHAR2(255);
ALTER TABLE horde_prefs MODIFY pref_scope VARCHAR2(16);
ALTER TABLE horde_prefs MODIFY pref_name VARCHAR2(32);
UPDATE horde_prefs SET pref_uid = RTRIM(pref_uid);
UPDATE horde_prefs SET pref_scope = RTRIM(pref_scope);
UPDATE horde_prefs SET pref_name = RTRIM(pref_name);

DELETE FROM horde_prefs WHERE pref_name = 'last_login' AND pref_scope = 'imp';

CREATE TABLE horde_datatree (
    datatree_id          NUMBER(16) NOT NULL,
    group_uid            VARCHAR2(255) NOT NULL,
    user_uid             VARCHAR2(255),
    datatree_name        VARCHAR2(255) NOT NULL,
    datatree_parents     VARCHAR2(255),
    datatree_order       NUMBER(16),
    datatree_data        CLOB,
    datatree_serialized  NUMBER(8) DEFAULT 0 NOT NULL,
    datatree_updated     DATE,

    PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_order_idx ON horde_datatree (datatree_order);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);

CREATE TABLE horde_datatree_attributes (
    datatree_id      NUMBER(16) NOT NULL,
    attribute_name   VARCHAR2(255) NOT NULL,
    attribute_key    VARCHAR2(255),
    attribute_value  VARCHAR2(4000)
);

CREATE INDEX datatree_attribute_idx ON horde_datatree_attributes (datatree_id);
CREATE INDEX datatree_attribute_name_idx ON horde_datatree_attributes (attribute_name);
CREATE INDEX datatree_attribute_key_idx ON horde_datatree_attributes (attribute_key);

CREATE TABLE horde_tokens (
    token_address    VARCHAR2(100) NOT NULL,
    token_id         VARCHAR2(32) NOT NULL,
    token_timestamp  NUMBER(16) NOT NULL,

    PRIMARY KEY (token_address, token_id)
);

CREATE TABLE horde_vfs (
    vfs_id        NUMBER(16) NOT NULL,
    vfs_type      NUMBER(8) NOT NULL,
    vfs_path      VARCHAR2(255),
    vfs_name      VARCHAR2(255) NOT NULL,
    vfs_modified  NUMBER(16) NOT NULL,
    vfs_owner     VARCHAR2(255),
    vfs_data      BLOB,

    PRIMARY KEY   (vfs_id)
);

CREATE INDEX vfs_path_idx ON horde_vfs (vfs_path);
CREATE INDEX vfs_name_idx ON horde_vfs (vfs_name);


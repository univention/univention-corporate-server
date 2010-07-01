-- $Horde: horde/scripts/upgrades/3.1_to_3.2.oci8.sql,v 1.2.2.16 2009-10-20 21:04:22 jan Exp $

CREATE TABLE horde_syncml_map (
    syncml_syncpartner VARCHAR2(255) NOT NULL,
    syncml_db          VARCHAR2(255) NOT NULL,
    syncml_uid         VARCHAR2(255) NOT NULL,
    syncml_cuid        VARCHAR2(255),
    syncml_suid        VARCHAR2(255),
    syncml_timestamp   NUMBER(16)
);

CREATE INDEX syncml_syncpartner_idx ON horde_syncml_map (syncml_syncpartner);
CREATE INDEX syncml_db_idx ON horde_syncml_map (syncml_db);
CREATE INDEX syncml_uid_idx ON horde_syncml_map (syncml_uid);
CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_cuid);
CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_suid);

CREATE TABLE horde_syncml_anchors(
    syncml_syncpartner  VARCHAR2(255) NOT NULL,
    syncml_db           VARCHAR2(255) NOT NULL,
    syncml_uid          VARCHAR2(255) NOT NULL,
    syncml_clientanchor VARCHAR2(255),
    syncml_serveranchor VARCHAR2(255)
);

CREATE INDEX syncml_anchors_syncpartner_idx ON horde_syncml_anchors (syncml_syncpartner);
CREATE INDEX syncml_anchors_db_idx ON horde_syncml_anchors (syncml_db);
CREATE INDEX syncml_anchors_uid_idx ON horde_syncml_anchors (syncml_uid);

-- delete old map entries from datatree
DELETE FROM horde_datatree WHERE group_uid = 'syncml';


CREATE TABLE horde_alarms (
    alarm_id        VARCHAR2(255) NOT NULL,
    alarm_uid       VARCHAR2(255),
    alarm_start     DATE NOT NULL,
    alarm_end       DATE,
    alarm_methods   VARCHAR2(255),
    alarm_params    CLOB,
    alarm_title     VARCHAR2(255) NOT NULL,
    alarm_text      CLOB,
    alarm_snooze    DATE,
    alarm_dismissed NUMBER(1) DEFAULT 0 NOT NULL,
    alarm_internal  CLOB
);

CREATE INDEX alarm_id_idx ON horde_alarms (alarm_id);
CREATE INDEX alarm_user_idx ON horde_alarms (alarm_uid);
CREATE INDEX alarm_start_idx ON horde_alarms (alarm_start);
CREATE INDEX alarm_end_idx ON horde_alarms (alarm_end);
CREATE INDEX alarm_snooze_idx ON horde_alarms (alarm_snooze);
CREATE INDEX alarm_dismissed_idx ON horde_alarms (alarm_dismissed);

CREATE TABLE horde_cache (
    cache_id          VARCHAR(32) NOT NULL,
    cache_timestamp   NUMBER(16) NOT NULL,
    cache_expiration  NUMBER(16) NOT NULL,
    cache_data        BLOB,
--
    PRIMARY KEY  (cache_id)
);

CREATE TABLE horde_groups (
    group_uid NUMBER(16) NOT NULL,
    group_name VARCHAR2(255) NOT NULL UNIQUE,
    group_parents VARCHAR2(255) NOT NULL,
    group_email VARCHAR2(255),
    PRIMARY KEY (group_uid)
);

CREATE TABLE horde_groups_members (
    group_uid NUMBER(16) NOT NULL,
    user_uid VARCHAR2(255) NOT NULL
);

CREATE INDEX group_uid_idx ON horde_groups_members (group_uid);
CREATE INDEX user_uid_idx ON horde_groups_members (user_uid);

CREATE TABLE horde_perms (
    perm_id NUMBER(16) NOT NULL,
    perm_name VARCHAR2(255) NOT NULL UNIQUE,
    perm_parents VARCHAR2(255) NOT NULL,
    perm_data CLOB,
    PRIMARY KEY (perm_id)
);

CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value);

CREATE TABLE horde_locks (
    lock_id                  VARCHAR2(36) NOT NULL,
    lock_owner               VARCHAR2(32) NOT NULL,
    lock_scope               VARCHAR2(32) NOT NULL,
    lock_principal           VARCHAR2(255) NOT NULL,
    lock_origin_timestamp    NUMBER(16) NOT NULL,
    lock_update_timestamp    NUMBER(16) NOT NULL,
    lock_expiry_timestamp    NUMBER(16) NOT NULL,
    lock_type                NUMBER(8) NOT NULL,
--
    PRIMARY KEY (lock_id)
);

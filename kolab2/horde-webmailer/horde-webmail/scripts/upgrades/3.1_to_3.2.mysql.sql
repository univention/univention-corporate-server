-- $Horde: horde/scripts/upgrades/3.1_to_3.2.mysql.sql,v 1.3.2.13 2008-06-11 08:06:12 jan Exp $

CREATE TABLE horde_syncml_map (
    syncml_syncpartner VARCHAR(255) NOT NULL,
    syncml_db          VARCHAR(255) NOT NULL,
    syncml_uid         VARCHAR(255) NOT NULL,
    syncml_cuid        VARCHAR(255),
    syncml_suid        VARCHAR(255),
    syncml_timestamp   INT
);

CREATE INDEX syncml_syncpartner_idx ON horde_syncml_map (syncml_syncpartner);
CREATE INDEX syncml_db_idx ON horde_syncml_map (syncml_db);
CREATE INDEX syncml_uid_idx ON horde_syncml_map (syncml_uid);
CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_cuid);
CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_suid);

CREATE TABLE horde_syncml_anchors(
    syncml_syncpartner  VARCHAR(255) NOT NULL,
    syncml_db           VARCHAR(255) NOT NULL,
    syncml_uid          VARCHAR(255) NOT NULL,
    syncml_clientanchor VARCHAR(255),
    syncml_serveranchor VARCHAR(255)
);

CREATE INDEX syncml_anchors_syncpartner_idx ON horde_syncml_anchors (syncml_syncpartner);
CREATE INDEX syncml_anchors_db_idx ON horde_syncml_anchors (syncml_db);
CREATE INDEX syncml_anchors_uid_idx ON horde_syncml_anchors (syncml_uid);

-- delete old map entries from datatree
DELETE FROM horde_datatree WHERE group_uid = 'syncml';

CREATE TABLE horde_alarms (
    alarm_id        VARCHAR(250) NOT NULL,
    alarm_uid       VARCHAR(250) NOT NULL,
    alarm_start     DATETIME NOT NULL,
    alarm_end       DATETIME,
    alarm_methods   VARCHAR(255),
    alarm_params    TEXT,
    alarm_title     VARCHAR(255) NOT NULL,
    alarm_text      TEXT,
    alarm_snooze    DATETIME,
    alarm_dismissed TINYINT(1) DEFAULT 0 NOT NULL,
    alarm_internal  TEXT
);

CREATE INDEX alarm_id_idx ON horde_alarms (alarm_id);
CREATE INDEX alarm_user_idx ON horde_alarms (alarm_uid);
CREATE INDEX alarm_start_idx ON horde_alarms (alarm_start);
CREATE INDEX alarm_end_idx ON horde_alarms (alarm_end);
CREATE INDEX alarm_snooze_idx ON horde_alarms (alarm_snooze);
CREATE INDEX alarm_dismissed_idx ON horde_alarms (alarm_dismissed);

CREATE TABLE horde_cache (
    cache_id          VARCHAR(32) NOT NULL,
    cache_timestamp   BIGINT NOT NULL,
    cache_expiration  BIGINT NOT NULL,
    cache_data        LONGBLOB,

    PRIMARY KEY  (cache_id)
);

CREATE TABLE horde_groups (
    group_uid INT(10) UNSIGNED NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    group_parents VARCHAR(255) NOT NULL,
    group_email VARCHAR(255),
    PRIMARY KEY (group_uid),
    UNIQUE KEY group_name (group_name)
);

CREATE TABLE horde_groups_members (
    group_uid INT(10) UNSIGNED NOT NULL,
    user_uid VARCHAR(255) NOT NULL
);
CREATE INDEX group_uid_idx ON horde_groups_members (group_uid);
CREATE INDEX user_uid_idx ON horde_groups_members (user_uid);

CREATE TABLE horde_perms (
    perm_id INT(11) NOT NULL,
    perm_name VARCHAR(255) NOT NULL,
    perm_parents VARCHAR(255) NOT NULL,
    perm_data TEXT,
    PRIMARY KEY (perm_id),
    UNIQUE KEY perm_name (perm_name)
);

CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value(255));

CREATE TABLE horde_locks (
    lock_id                  VARCHAR(36) NOT NULL,
    lock_owner               VARCHAR(32) NOT NULL,
    lock_scope               VARCHAR(32) NOT NULL,
    lock_principal           VARCHAR(255) NOT NULL,
    lock_origin_timestamp    BIGINT NOT NULL,
    lock_update_timestamp    BIGINT NOT NULL,
    lock_expiry_timestamp    BIGINT NOT NULL,
    lock_type                TINYINT NOT NULL,

    PRIMARY KEY (lock_id)
);

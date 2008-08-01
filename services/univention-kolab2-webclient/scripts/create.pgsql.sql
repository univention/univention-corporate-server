-- $Horde: horde/scripts/sql/create.pgsql.sql,v 1.1.10.7 2008/03/12 17:43:50 chuck Exp $
--
-- Uncomment the ALTER line below and change the password.  Then run as:
--
-- $ psql -d template1 -f create.pgsql.sql


CREATE TABLE horde_users (
    user_uid                    VARCHAR(255) NOT NULL,
    user_pass                   VARCHAR(255) NOT NULL,
    user_soft_expiration_date   INTEGER,
    user_hard_expiration_date   INTEGER,
--
    PRIMARY KEY (user_uid)
);

CREATE TABLE horde_prefs (
    pref_uid        VARCHAR(255) NOT NULL,
    pref_scope      VARCHAR(16) DEFAULT '' NOT NULL,
    pref_name       VARCHAR(32) NOT NULL,
    pref_value      TEXT,
--
    PRIMARY KEY (pref_uid, pref_scope, pref_name)
);

CREATE INDEX pref_uid_idx ON horde_prefs (pref_uid);
CREATE INDEX pref_scope_idx ON horde_prefs (pref_scope);

CREATE TABLE horde_datatree (
    datatree_id INT NOT NULL,
    group_uid VARCHAR(255) NOT NULL,
    user_uid VARCHAR(255) NOT NULL,
    datatree_name VARCHAR(255) NOT NULL,
    datatree_parents VARCHAR(255) NOT NULL,
    datatree_order INT,
    datatree_data TEXT,
    datatree_serialized SMALLINT DEFAULT 0 NOT NULL,

    PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_order_idx ON horde_datatree (datatree_order);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);
CREATE INDEX datatree_parents_idx ON horde_datatree (datatree_parents);

CREATE TABLE horde_datatree_attributes (
    datatree_id INT NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_key VARCHAR(255),
    attribute_value TEXT
);

CREATE INDEX datatree_attribute_idx ON horde_datatree_attributes USING HASH(datatree_id);
CREATE INDEX datatree_attribute_name_idx ON horde_datatree_attributes (attribute_name);
CREATE INDEX datatree_attribute_key_idx ON horde_datatree_attributes (attribute_key);
CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value);

CREATE TABLE horde_tokens (
    token_address    VARCHAR(100) NOT NULL,
    token_id         VARCHAR(32) NOT NULL,
    token_timestamp  BIGINT NOT NULL,
--
    PRIMARY KEY (token_address, token_id)
);

CREATE TABLE horde_vfs (
    vfs_id        BIGINT NOT NULL,
    vfs_type      SMALLINT NOT NULL,
    vfs_path      VARCHAR(255) NOT NULL,
    vfs_name      VARCHAR(255) NOT NULL,
    vfs_modified  BIGINT NOT NULL,
    vfs_owner     VARCHAR(255) NOT NULL,
    vfs_data      TEXT,

    PRIMARY KEY   (vfs_id)
);

CREATE INDEX vfs_path_idx ON horde_vfs (vfs_path);
CREATE INDEX vfs_name_idx ON horde_vfs (vfs_name);

CREATE TABLE horde_histories (
    history_id       BIGINT NOT NULL,
    object_uid       VARCHAR(255) NOT NULL,
    history_action   VARCHAR(32) NOT NULL,
    history_ts       BIGINT NOT NULL,
    history_desc     TEXT,
    history_who      VARCHAR(255),
    history_extra    TEXT,
--
    PRIMARY KEY (history_id)
);

CREATE INDEX history_action_idx ON horde_histories (history_action);
CREATE INDEX history_ts_idx ON horde_histories (history_ts);
CREATE INDEX history_uid_idx ON horde_histories (object_uid);

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR(32) NOT NULL,
    session_lastmodified   BIGINT NOT NULL,
    session_data           TEXT,
    PRIMARY KEY (session_id)
);

CREATE TABLE horde_syncml_map (
    syncml_syncpartner VARCHAR(64) NOT NULL,
    syncml_db          VARCHAR(64) NOT NULL,
    syncml_uid         VARCHAR(64) NOT NULL,
    syncml_cuid        VARCHAR(64),
    syncml_suid        VARCHAR(64),
    syncml_timestamp   BIGINT
);

CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_syncpartner, syncml_db, syncml_uid, syncml_cuid);
CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_syncpartner, syncml_db, syncml_uid, syncml_suid);

CREATE TABLE horde_alarms (
    alarm_id        VARCHAR(255) NOT NULL,
    alarm_uid       VARCHAR(255),
    alarm_start     TIMESTAMP NOT NULL,
    alarm_end       TIMESTAMP,
    alarm_methods   VARCHAR(255),
    alarm_params    TEXT,
    alarm_title     VARCHAR(255) NOT NULL,
    alarm_text      TEXT,
    alarm_snooze    TIMESTAMP,
    alarm_dismissed SMALLINT DEFAULT 0 NOT NULL,
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
    cache_data        TEXT,
--
    PRIMARY KEY  (cache_id)
);

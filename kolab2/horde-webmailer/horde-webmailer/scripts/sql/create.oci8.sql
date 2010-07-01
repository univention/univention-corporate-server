set doc off;
set sqlblanklines on;

/**
 * Oracle Table Creation Scripts.
 * 
 * $Horde: horde/scripts/sql/create.oci8.sql,v 1.4.8.24 2009-10-19 10:54:32 jan Exp $
 * 
 * @author Miguel Ward <mward@aluar.com.ar>
 * 
 * This sql creates the Horde SQL tables in an Oracle 8.x database. Should
 * work with Oracle 9.x (and Oracle7 using varchar2).
 * 
 * Notes:
 * 
 *  * Obviously you must have Oracle installed on this machine AND you must
 *    have compiled PHP with Oracle (you included --with-oci8-instant
 *    --with-oci8 or in the build arguments for PHP, or uncommented the oci8
 *    extension in php.ini).
 * 
 *  * If you don't use the Instant Client, make sure that the user that starts
 *    up Apache (usually nobody or www-data) has the following environment
 *    variables defined:
 * 
 *    export ORACLE_HOME=/home/oracle/OraHome1
 *    export ORA_NLS=/home/oracle/OraHome1/ocommon/nls/admin/data
 *    export ORA_NLS33=/home/oracle/OraHome1/ocommon/nls/admin/data
 *    export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
 * 
 *    YOU MUST CUSTOMIZE THESE VALUES TO BE APPROPRIATE TO YOUR INSTALLATION
 * 
 *    You can include these variables in the user's local .profile or in
 *    /etc/profile, etc.
 * 
 *  * No grants are necessary since we connect as the owner of the tables. If
 *    you wish you can adapt the creation of tables to include tablespace and
 *    storage information. Since we include none it will use the default
 *    tablespace values for the user creating these tables. Same with the
 *    indexes (in theory these should use a different tablespace).
 * 
 *  * There is no need to shut down and start up the database!
 */

rem conn horde/&horde_password@database

/**
 * This is the Horde users table, needed only if you are using SQL
 * authentication.
 */

CREATE TABLE horde_users (
    user_uid                    VARCHAR2(255) NOT NULL,
    user_pass                   VARCHAR2(255) NOT NULL,
    user_soft_expiration_date   NUMBER(16),
    user_hard_expiration_date   NUMBER(16),

    PRIMARY KEY (user_uid)
);

CREATE TABLE horde_signups (
    user_name VARCHAR2(255) NOT NULL,
    signup_date NUMBER(16) NOT NULL,
    signup_host VARCHAR2(255) NOT NULL,
    signup_data CLOB NOT NULL,
    PRIMARY KEY (user_name)
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

/**
 * This is the Horde preferences table, holding all of the user-specific
 * options for every Horde user.
 * 
 * pref_uid   is the username.
 * pref_scope is the application the pref belongs to.
 * pref_name  is the name of the variable to save.
 * pref_value is the value saved (can be very long).
 * 
 * We use a CLOB column so that longer column values are supported.
 * 
 * If still using Oracle 7 this should work but you have to use
 * VARCHAR2(2000) which is the limit imposed by said version.
 */

CREATE TABLE horde_prefs (
    pref_uid    VARCHAR2(255) NOT NULL,
    pref_scope  VARCHAR2(16) NOT NULL,
    pref_name   VARCHAR2(32) NOT NULL,
--  See above notes on CLOBs.
    pref_value  CLOB,

    PRIMARY KEY (pref_uid, pref_scope, pref_name)
);

CREATE INDEX pref_uid_idx ON horde_prefs (pref_uid);
CREATE INDEX pref_scope_idx ON horde_prefs (pref_scope);


/**
 * The DataTree tables are used for holding hierarchical data such as Groups,
 * Permissions, and data for some Horde applications.
 */

CREATE TABLE horde_datatree (
    datatree_id          NUMBER(16) NOT NULL,
    group_uid            VARCHAR2(255) NOT NULL,
    user_uid             VARCHAR2(255),
    datatree_name        VARCHAR2(255) NOT NULL,
    datatree_parents     VARCHAR2(255),
    datatree_order       NUMBER(16),
    datatree_data        CLOB,
    datatree_serialized  NUMBER(1) DEFAULT 0 NOT NULL,

    PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_order_idx ON horde_datatree (datatree_order);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);
CREATE INDEX datatree_parents_idx ON horde_datatree (datatree_parents);

CREATE TABLE horde_datatree_attributes (
    datatree_id      NUMBER(16) NOT NULL,
    attribute_name   VARCHAR2(255) NOT NULL,
    attribute_key    VARCHAR2(255),
    attribute_value  VARCHAR2(4000)
);

CREATE INDEX datatree_attribute_idx ON horde_datatree_attributes (datatree_id);
CREATE INDEX datatree_attribute_name_idx ON horde_datatree_attributes (attribute_name);
CREATE INDEX datatree_attribute_key_idx ON horde_datatree_attributes (attribute_key);
CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value);


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


CREATE TABLE horde_histories (
    history_id       NUMBER(16) NOT NULL,
    object_uid       VARCHAR2(255) NOT NULL,
    history_action   VARCHAR2(32) NOT NULL,
    history_ts       NUMBER(16) NOT NULL,
    history_desc     CLOB,
    history_who      VARCHAR2(255),
    history_extra    CLOB,

    PRIMARY KEY (history_id)
);

CREATE INDEX history_action_idx ON horde_histories (history_action);
CREATE INDEX history_ts_idx ON horde_histories (history_ts);
CREATE INDEX history_uid_idx ON horde_histories (object_uid);


CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR2(32) NOT NULL,
    session_lastmodified   NUMBER(16) NOT NULL,
    session_data           BLOB,

    PRIMARY KEY (session_id)
);

CREATE INDEX session_lastmodified_idx ON horde_sessionhandler (session_lastmodified);


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
    cache_id          VARCHAR2(32) NOT NULL,
    cache_timestamp   NUMBER(16) NOT NULL,
    cache_expiration  NUMBER(16) NOT NULL,
    cache_data        BLOB,
--
    PRIMARY KEY  (cache_id)
);

CREATE TABLE horde_locks (
    lock_id                  VARCHAR2(36) NOT NULL,
    lock_owner               VARCHAR2(32) NOT NULL,
    lock_scope               VARCHAR2(32) NOT NULL,
    lock_principal           VARCHAR2(255) NOT NULL,
    lock_origin_timestamp    NUMBER(16) NOT NULL,
    lock_update_timestamp    NUMBER(16) NOT NULL,
    lock_expiry_timestamp    NUMBER(16) NOT NULL,
    lock_type                NUMBER(8) NOT NULL,

    PRIMARY KEY (lock_id)
);

exit

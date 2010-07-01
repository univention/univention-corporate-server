-- $Horde: horde/scripts/sql/create.sybase.sql,v 1.1.10.18 2009-06-10 16:45:28 jan Exp $
--
-- horde tables definitions : sql script
-- 01/22/2003 - F. Helly <francois.helly@wanadoo.fr>
-- command line syntax :  isql -ihorde_sybase.sql
-- warning : use nvarchar only if you need unicode encoding for some strings

use horde
go


DROP TABLE horde_datatree
go

DROP TABLE horde_prefs
go

DROP TABLE horde_users
go

DROP TABLE horde_signups
go

DROP TABLE horde_groups
go

DROP TABLE horde_groups_members
go

DROP TABLE horde_sessionhandler
go

-- DROP TABLE horde_datatree_seq
-- go

-- DROP TABLE horde_tokens
-- go

-- DROP TABLE horde_vfs
-- go

-- DROP TABLE horde_muvfs
-- go


CREATE TABLE horde_users (
    user_uid varchar(256) NOT NULL,
    user_pass varchar(256) NOT NULL,
    user_soft_expiration_date numeric(10,0),
    user_hard_expiration_date numeric(10,0),
    PRIMARY KEY (user_uid)
)
go

CREATE TABLE horde_signups (
    user_name VARCHAR(255) NOT NULL,
    signup_date NUMERIC(10,0) NOT NULL,
    signup_host VARCHAR(255) NOT NULL,
    signup_data TEXT NOT NULL,
    PRIMARY KEY (user_name)
)
go

CREATE TABLE horde_groups (
    group_uid numeric(11,0) IDENTITY NOT NULL,
    group_name varchar(256) NOT NULL,
    group_parents varchar(256) NOT NULL,
    group_email varchar(256),
    PRIMARY KEY (group_uid)
)
go

CREATE TABLE horde_groups_members (
    group_uid numeric(11,0) NOT NULL,
    user_uid varchar(256) NOT NULL
)
go

CREATE INDEX group_uid_idx ON horde_groups_members (group_uid)
CREATE INDEX user_uid_idx ON horde_groups_members (user_uid)
go

CREATE TABLE horde_perms (
    perm_id numeric(11,0) NOT NULL,
    perm_name varchar(256) NOT NULL,
    perm_parents varchar(256) NOT NULL,
    perm_data text,
    PRIMARY KEY (perm_id)
)
go

CREATE TABLE horde_datatree (
    datatree_id numeric(11,0) IDENTITY NOT NULL,
    group_uid varchar(256) NOT NULL,
    user_uid varchar(256) NOT NULL,
    datatree_name varchar(256) NOT NULL,
    datatree_parents varchar(256) NULL,
    datatree_data text NULL,
    datatree_serialized smallint DEFAULT 0 NOT NULL,
    PRIMARY KEY (datatree_id),
    FOREIGN KEY (user_uid)
    REFERENCES horde_users(user_uid)
)
go

CREATE TABLE horde_prefs (
    pref_uid varchar(256) NOT NULL,
    pref_scope varchar(16) NOT NULL,
    pref_name varchar(32) NOT NULL,
    pref_value text NULL,
    PRIMARY KEY (pref_uid,pref_scope,pref_name)
)
go

CREATE TABLE horde_sessionhandler (
    session_id varchar(32) NOT NULL,
    session_lastmodified numeric(11,0) NOT NULL,
    session_data image NULL,
    PRIMARY KEY (session_id)
)
go

CREATE TABLE horde_syncml_map (
    syncml_syncpartner varchar(255) NOT NULL,
    syncml_db          varchar(255) NOT NULL,
    syncml_uid         varchar(255) NOT NULL,
    syncml_cuid        varchar(255),
    syncml_suid        varchar(255),
    syncml_timestamp   numeric(11,0)
);
go

CREATE TABLE horde_syncml_anchors(
    syncml_syncpartner  varchar(255) NOT NULL,
    syncml_db           varchar(255) NOT NULL,
    syncml_uid          varchar(255) NOT NULL,
    syncml_clientanchor varchar(255),
    syncml_serveranchor varchar(255)
);
go

CREATE TABLE horde_alarms (
    alarm_id        varchar(255) NOT NULL,
    alarm_uid       varchar(255),
    alarm_start     timestamp NOT NULL,
    alarm_end       timestamp,
    alarm_methods   varchar(255),
    alarm_params    text,
    alarm_title     varchar(255) NOT NULL,
    alarm_text      text,
    alarm_snooze    timestamp,
    alarm_dismissed smallint DEFAULT 0 NOT NULL,
    alarm_internal  text
)
go

CREATE TABLE horde_cache (
    cache_id          varchar(32) NOT NULL,
    cache_timestamp   numeric(11,0) NOT NULL,
    cache_expiration  numeric(11,0) NOT NULL,
    cache_data        image,
    PRIMARY KEY  (cache_id)
)
go

CREATE TABLE horde_locks (
    lock_id                  varchar(36) NOT NULL,
    lock_owner               varchar(32) NOT NULL,
    lock_scope               varchar(32) NOT NULL,
    lock_principal           varchar(255) NOT NULL,
    lock_origin_timestamp    numeric(11, 0) NOT NULL,
    lock_update_timestamp    numeric(11, 0) NOT NULL,
    lock_expiry_timestamp    numeric(11, 0) NOT NULL,
    lock_type                numeric(11, 0) NOT NULL,

    PRIMARY KEY (lock_id)
)
go

-- CREATE TABLE horde_datatree_seq (
--   id numeric(10,0) IDENTITY NOT NULL,
--   PRIMARY KEY (id)
-- )
-- go

-- CREATE TABLE horde_tokens (
--   token_address varchar(100) NOT NULL,
--   token_id varchar(32) NOT NULL,
--   token_timestamp numeric(20,0) NOT NULL,
--   PRIMARY KEY (token_address,token_id)
-- )
-- go

-- CREATE TABLE horde_vfs (
--   vfs_id numeric(20,0) NOT NULL,
--   vfs_type numeric(8,0) NOT NULL,
--   vfs_path varchar(256) NOT NULL,
--   vfs_name nvarchar(256) NOT NULL,
--   vfs_modified numeric(20,0) NOT NULL,
--   vfs_owner varchar(256) NOT NULL,
--   vfs_data image NULL,
--   PRIMARY KEY (vfs_id)
-- )
-- go

-- CREATE TABLE horde_muvfs (
--   vfs_id  numeric(20,0) NOT NULL,
--   vfs_type      numeric(8,0) NOT NULL,
--   vfs_path      varchar(256) NOT NULL,
--   vfs_name      varchar(256) NOT NULL,
--   vfs_modified  numeric(8,0) NOT NULL,
--   vfs_owner     varchar(256) NOT NULL,
--   vfs_perms     smallint NOT NULL,
--   vfs_data      image NULL,
--   PRIMARY KEY (vfs_id)
--   )
-- go


CREATE INDEX pref_uid_idx ON horde_prefs (pref_uid)
go

CREATE INDEX pref_scope_idx ON horde_prefs (pref_scope)
go

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name)
go

CREATE INDEX datatree_group_idx ON horde_datatree (group_uid)
go

CREATE INDEX datatree_user_idx ON horde_datatree (user_uid)
go

CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized)
go

CREATE INDEX datatree_parents_idx ON horde_datatree (datatree_parents)
go

CREATE INDEX syncml_syncpartner_idx ON horde_syncml_map (syncml_syncpartner);
go

CREATE INDEX syncml_db_idx ON horde_syncml_map (syncml_db);
go

CREATE INDEX syncml_uid_idx ON horde_syncml_map (syncml_uid);
go

CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_cuid);
go

CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_suid);
go

CREATE INDEX syncml_anchors_syncpartner_idx ON horde_syncml_anchors (syncml_syncpartner);
go

CREATE INDEX syncml_anchors_db_idx ON horde_syncml_anchors (syncml_db);
go

CREATE INDEX syncml_anchors_uid_idx ON horde_syncml_anchors (syncml_uid);
go

CREATE INDEX alarm_id_idx ON horde_alarms (alarm_id)
go

CREATE INDEX alarm_user_idx ON horde_alarms (alarm_uid)
go

CREATE INDEX alarm_start_idx ON horde_alarms (alarm_start)
go

CREATE INDEX alarm_end_idx ON horde_alarms (alarm_end)
go

CREATE INDEX alarm_snooze_idx ON horde_alarms (alarm_snooze)
go

CREATE INDEX alarm_dismissed_idx ON horde_alarms (alarm_dismissed)
go

CREATE INDEX session_lastmodified_idx ON horde_sessionhandler (session_lastmodified)
go

-- CREATE INDEX vfs_path_idx ON horde_vfs (vfs_path)
-- go

-- CREATE INDEX vfs_name_idx ON horde_vfs (vfs_name)
-- go

-- CREATE INDEX vfs_path_idx ON horde_muvfs (vfs_path)
-- go

-- CREATE INDEX vfs_name_idx ON horde_muvfs (vfs_name)
-- go


grant select, insert, delete, update on editor to horde
go
grant select, insert, delete, update on host to horde
go
grant select, insert, delete, update on dbase to horde
go
grant select, insert, delete, update on site to horde
go
grant select, insert, delete, update on connection to horde
go
grant select, insert, delete, update on horde_datatree to horde
go
grant select, insert, delete, update on horde_prefs to horde
go
grant select, insert, delete, update on horde_sessionhandler to horde
go
grant select, insert, delete, update on horde_syncml_map to horde
go
grant select, insert, delete, update on horde_alarms to horde
go
grant select, insert, delete, update on horde_cache to horde
go

-- grant select, insert, delete, update on horde_datatree_seq to horde
-- go
-- grant select, insert, delete, update on horde_tokens to horde
-- go
-- grant select, insert, delete, update on horde_vfs to horde
-- go
-- grant select, insert, delete, update on horde_muvfs to horde
-- go



-- add you admin_user_uid and admin_user_pass

-- insert into horde_users values ('your_admin_user_uid', 'your_admin_user_pass_md5_encrypted')
-- go

-- $Horde: horde/scripts/upgrades/3.1_to_3.2.sybase.sql,v 1.2.2.15 2008-06-11 08:06:12 jan Exp $

CREATE TABLE horde_syncml_map (
    syncml_syncpartner varchar(255) NOT NULL,
    syncml_db          varchar(255) NOT NULL,
    syncml_uid         varchar(255) NOT NULL,
    syncml_cuid        varchar(255),
    syncml_suid        varchar(255),
    syncml_timestamp   numeric(11,0)
);
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

CREATE TABLE horde_syncml_anchors(
    syncml_syncpartner  varchar(255) NOT NULL,
    syncml_db           varchar(255) NOT NULL,
    syncml_uid          varchar(255) NOT NULL,
    syncml_clientanchor varchar(255),
    syncml_serveranchor varchar(255)
);
go

CREATE INDEX syncml_anchors_syncpartner_idx ON horde_syncml_anchors (syncml_syncpartner);
go

CREATE INDEX syncml_anchors_db_idx ON horde_syncml_anchors (syncml_db);
go

CREATE INDEX syncml_anchors_uid_idx ON horde_syncml_anchors (syncml_uid);
go

DELETE FROM horde_datatree WHERE group_uid = 'syncml';
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


CREATE TABLE horde_cache (
    cache_id          varchar(32) NOT NULL,
    cache_timestamp   numeric(11,0) NOT NULL,
    cache_expiration  numeric(11,0) NOT NULL,
    cache_data        image,
    PRIMARY KEY  (cache_id)
);
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


CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value)
go


grant select, insert, delete, update on horde_syncml_map to horde
go
grant select, insert, delete, update on horde_alarms to horde
go
grant select, insert, delete, update on horde_cache to horde
go
grant select, insert, delete, update on horde_groups to horde
go
grant select, insert, delete, update on horde_groups_members to horde
go
grant select, insert, delete, update on horde_perms to horde
go

create table horde_locks (
    lock_id                  varchar(36) not null,
    lock_owner               varchar(32) not null,
    lock_scope               varchar(32) not null,
    lock_principal           varchar(255) not null,
    lock_origin_timestamp    numeric(11, 0) not null,
    lock_update_timestamp    numeric(11, 0) not null,
    lock_expiry_timestamp    numeric(11, 0) not null,
    lock_type                numeric(11, 0) not null,

    PRIMARY KEY (lock_id)
)
go

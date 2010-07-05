-- $Horde: kronolith/scripts/sql/kronolith.oci8.sql,v 1.4.2.15 2009-10-22 16:48:56 jan Exp $

CREATE TABLE kronolith_events (
    event_id VARCHAR2(32) NOT NULL,
    event_uid VARCHAR2(255) NOT NULL,
    calendar_id VARCHAR2(255) NOT NULL,
    event_creator_id VARCHAR2(255) NOT NULL,
    event_description VARCHAR2(4000),
    event_location VARCHAR2(4000),
    event_status NUMBER(8) DEFAULT 0,
    event_attendees VARCHAR2(4000),
    event_keywords VARCHAR2(4000),
    event_exceptions VARCHAR2(4000),
    event_title VARCHAR2(255),
    event_category VARCHAR2(80),
    event_recurtype NUMBER(8) DEFAULT 0,
    event_recurinterval NUMBER(16),
    event_recurdays NUMBER(16),
    event_recurenddate DATE,
    event_recurcount NUMBER(8),
    event_start DATE,
    event_end DATE,
    event_alarm NUMBER(16) DEFAULT 0,
    event_modified NUMBER(16) NOT NULL,
    event_private NUMBER(1) DEFAULT 0 NOT NULL,
--
    PRIMARY KEY (event_id)
);

CREATE INDEX kronolith_calendar_idx ON kronolith_events (calendar_id);
CREATE INDEX kronolith_uid_idx ON kronolith_events (event_uid);


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR2(255),
    vfb_email      VARCHAR2(255) NOT NULL,
    vfb_serialized VARCHAR2(4000) NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);


CREATE TABLE kronolith_shares (
    share_id NUMBER(16) NOT NULL,
    share_name VARCHAR2(255) NOT NULL,
    share_owner VARCHAR2(255) NOT NULL,
    share_flags NUMBER(8) DEFAULT 0 NOT NULL,
    perm_creator NUMBER(8) DEFAULT 0 NOT NULL,
    perm_default NUMBER(8) DEFAULT 0 NOT NULL,
    perm_guest NUMBER(8) DEFAULT 0 NOT NULL,
    attribute_name VARCHAR2(255) NOT NULL,
    attribute_desc VARCHAR2(255),
    PRIMARY KEY (share_id)
);

CREATE INDEX kronolith_share_name_idx ON kronolith_shares (share_name);
CREATE INDEX kronolith_share_owner_idx ON kronolith_shares (share_owner);
CREATE INDEX kronolith_perm_creator_idx ON kronolith_shares (perm_creator);
CREATE INDEX kronolith_perm_default_idx ON kronolith_shares (perm_default);
CREATE INDEX kronolith_perm_guest_idx ON kronolith_shares (perm_guest);

CREATE TABLE kronolith_shares_groups (
    share_id NUMBER(16) NOT NULL,
    group_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX kronolith_groups_share_id_idx ON kronolith_shares_groups (share_id);
CREATE INDEX kronolith_groups_group_uid_idx ON kronolith_shares_groups (group_uid);
CREATE INDEX kronolith_groups_perm_idx ON kronolith_shares_groups (perm);

CREATE TABLE kronolith_shares_users (
    share_id NUMBER(16) NOT NULL,
    user_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX kronolith_users_share_id_idx ON kronolith_shares_users (share_id);
CREATE INDEX kronolith_users_user_uid_idx ON kronolith_shares_users (user_uid);
CREATE INDEX kronolith_users_perm_idx ON kronolith_shares_users (perm);

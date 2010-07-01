-- $Horde: horde/scripts/sql/horde_groups.oci8.sql,v 1.1.2.3 2009-10-19 10:54:33 jan Exp $

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

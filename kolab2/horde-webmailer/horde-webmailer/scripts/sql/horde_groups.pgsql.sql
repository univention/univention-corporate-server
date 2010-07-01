-- $Horde: horde/scripts/sql/horde_groups.pgsql.sql,v 1.1.2.2 2008-04-28 03:24:02 chuck Exp $

CREATE TABLE horde_groups (
    group_uid INTEGER NOT NULL,
    group_name VARCHAR(255) NOT NULL UNIQUE,
    group_parents VARCHAR(255) NOT NULL,
    group_email VARCHAR(255),
    PRIMARY KEY (group_uid)
);

CREATE TABLE horde_groups_members (
    group_uid INTEGER NOT NULL,
    user_uid VARCHAR(255) NOT NULL
);
CREATE INDEX group_uid_idx ON horde_groups_members (group_uid);
CREATE INDEX user_uid_idx ON horde_groups_members (user_uid);

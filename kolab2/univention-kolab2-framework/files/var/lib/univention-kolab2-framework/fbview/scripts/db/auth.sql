-- $Horde: horde/scripts/db/auth.sql,v 1.10 2003/07/14 16:33:07 mdjukic Exp $

CREATE TABLE horde_users (
    user_uid   VARCHAR(255) NOT NULL,
    user_pass  VARCHAR(32) NOT NULL,

    PRIMARY KEY (user_uid)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_users TO horde;

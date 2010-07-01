-- $Horde: horde/scripts/sql/horde_users.sql,v 1.2.10.3 2007-12-20 15:03:03 jan Exp $

CREATE TABLE horde_users (
    user_uid                    VARCHAR(255) NOT NULL,
    user_pass                   VARCHAR(255) NOT NULL,
    user_soft_expiration_date   INTEGER,
    user_hard_expiration_date   INTEGER,
--
    PRIMARY KEY (user_uid)
);

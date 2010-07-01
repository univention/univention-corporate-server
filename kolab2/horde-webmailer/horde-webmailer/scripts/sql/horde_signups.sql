-- $Horde: horde/scripts/sql/horde_signups.sql,v 1.1.2.2 2009-06-10 16:45:28 jan Exp $
CREATE TABLE horde_signups (
    user_name VARCHAR(255) NOT NULL,
    signup_date INTEGER NOT NULL,
    signup_host VARCHAR(255) NOT NULL,
    signup_data TEXT NOT NULL,
    PRIMARY KEY (user_name)
);

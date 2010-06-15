-- $Horde: horde/scripts/db/sessionhandler_pgsql.sql,v 1.1 2003/12/16 04:24:49 chuck Exp $

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR(32) NOT NULL,
    session_lastmodified   INT NOT NULL,
    session_data           TEXT,
    PRIMARY KEY (session_id)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_sessionhandler TO horde;
-- $Horde: horde/scripts/db/sessionhandler.sql,v 1.4 2003/07/14 16:33:08 mdjukic Exp $

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR(32) NOT NULL,
    session_lastmodified   INT NOT NULL,
    session_data           LONGBLOB,
-- Or, on some DBMS systems:
--  session_data           IMAGE,

    PRIMARY KEY (session_id)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_sessionhandler TO horde;

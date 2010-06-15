-- $Horde: horde/scripts/db/sessionhandler_sapdb.sql,v 1.1 2002/09/08 22:59:15 mikec Exp $

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR(32) NOT NULL,
    session_lastmodified   INT NOT NULL,
    session_data           LONG BYTE,
    PRIMARY KEY (session_id)
)

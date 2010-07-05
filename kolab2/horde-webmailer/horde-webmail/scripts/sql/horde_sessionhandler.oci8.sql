-- $Horde: horde/scripts/sql/horde_sessionhandler.oci8.sql,v 1.2.10.4 2009-10-19 10:54:33 jan Exp $

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR2(32) NOT NULL,
    session_lastmodified   NUMBER(16) NOT NULL,
    session_data           BLOB,
--
    PRIMARY KEY (session_id)
);

CREATE INDEX session_lastmodified_idx ON horde_sessionhandler (session_lastmodified);

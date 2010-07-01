-- $Horde: horde/scripts/sql/horde_sessionhandler.mysql.sql,v 1.1.2.3 2009-02-14 04:43:47 chuck Exp $

CREATE TABLE horde_sessionhandler (
    session_id             VARCHAR(32) NOT NULL,
    session_lastmodified   INT NOT NULL,
    session_data           LONGBLOB,

    PRIMARY KEY (session_id)
) ENGINE = InnoDB;

CREATE INDEX session_lastmodified_idx ON horde_sessionhandler (session_lastmodified);

-- $Horde: horde/scripts/db/log.sql,v 1.3 2003/07/28 13:40:39 chuck Exp $

CREATE TABLE horde_log (
    id          INT NOT NULL,
    logtime     TIMESTAMP NOT NULL,
    ident       CHAR(16) NOT NULL,
    priority    INT NOT NULL,
    -- For DBs that don't support the TEXT field type:
    -- message  VARCHAR(2048),
    message     TEXT,
    PRIMARY KEY (id)
);

GRANT INSERT ON horde_log TO horde;

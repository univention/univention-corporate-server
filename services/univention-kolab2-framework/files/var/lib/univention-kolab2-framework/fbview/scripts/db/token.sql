-- $Horde: horde/scripts/db/token.sql,v 1.3 2003/07/14 16:33:08 mdjukic Exp $

CREATE TABLE horde_tokens (
    token_address    VARCHAR(8) NOT NULL,
    token_id         VARCHAR(32) NOT NULL,
    token_timestamp  BIGINT NOT NULL,

    PRIMARY KEY (token_address, token_id)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_tokens TO horde;

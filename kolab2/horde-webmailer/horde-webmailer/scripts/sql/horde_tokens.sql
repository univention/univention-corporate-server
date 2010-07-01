-- $Horde: horde/scripts/sql/horde_tokens.sql,v 1.2.10.3 2007-12-20 15:03:03 jan Exp $

CREATE TABLE horde_tokens (
    token_address    VARCHAR(100) NOT NULL,
    token_id         VARCHAR(32) NOT NULL,
    token_timestamp  BIGINT NOT NULL,
--
    PRIMARY KEY (token_address, token_id)
);

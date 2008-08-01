-- $Horde: mnemo/scripts/sql/mnemo.sql,v 1.5 2004/12/21 15:55:24 chuck Exp $

CREATE TABLE mnemo_memos (
    memo_owner      VARCHAR(255) NOT NULL,
    memo_id         VARCHAR(32) NOT NULL,
    memo_uid        VARCHAR(255) NOT NULL,
    memo_desc       VARCHAR(64) NOT NULL,
    memo_body       TEXT,
    memo_category   VARCHAR(80),
    memo_private    SMALLINT NOT NULL DEFAULT 0,
--
    PRIMARY KEY (memo_owner, memo_id)
);

ALTER TABLE mnemo_memos OWNER TO horde;

CREATE INDEX mnemo_notepad_idx ON mnemo_memos (memo_owner);
CREATE INDEX mnemo_uid_idx ON mnemo_memos (memo_uid);

GRANT SELECT, INSERT, UPDATE, DELETE ON mnemo_memos TO horde;

-- $Horde: horde/scripts/sql/horde_histories.mssql.sql,v 1.1.2.3 2008-07-20 14:25:23 chuck Exp $

CREATE TABLE horde_histories (
    history_id       INT UNSIGNED NOT NULL,
    object_uid       VARCHAR(255) NOT NULL,
    history_action   VARCHAR(32) NOT NULL,
    history_ts       BIGINT NOT NULL,
    history_desc     VARCHAR(MAX),
    history_who      VARCHAR(255),
    history_extra    VARCHAR(MAX),
--
    PRIMARY KEY (history_id)
);

CREATE INDEX history_action_idx ON horde_histories (history_action);
CREATE INDEX history_ts_idx ON horde_histories (history_ts);
CREATE INDEX history_uid_idx ON horde_histories (object_uid);

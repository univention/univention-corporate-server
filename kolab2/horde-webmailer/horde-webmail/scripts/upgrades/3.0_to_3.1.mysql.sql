-- $Horde: horde/scripts/upgrades/3.0_to_3.1.mysql.sql,v 1.1.2.2 2007-12-20 15:03:04 jan Exp $
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 3.0_to_3.1.mysql.sql

ALTER TABLE horde_users ADD COLUMN user_soft_expiration_date INT;
ALTER TABLE horde_users ADD COLUMN user_hard_expiration_date INT;

CREATE TABLE horde_histories (
    history_id       BIGINT NOT NULL,
    object_uid       VARCHAR(255) NOT NULL,
    history_action   VARCHAR(32) NOT NULL,
    history_ts       BIGINT NOT NULL,
    history_desc     TEXT,
    history_who      VARCHAR(255),
    history_extra    TEXT,
--
    PRIMARY KEY (history_id)
);

CREATE INDEX history_action_idx ON horde_histories (history_action);
CREATE INDEX history_ts_idx ON horde_histories (history_ts);
CREATE INDEX history_uid_idx ON horde_histories (object_uid);

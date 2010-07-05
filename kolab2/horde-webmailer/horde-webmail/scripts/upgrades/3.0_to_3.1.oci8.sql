-- $Horde: horde/scripts/upgrades/3.0_to_3.1.oci8.sql,v 1.1.2.2 2007-12-20 15:03:04 jan Exp $

ALTER TABLE horde_users ADD user_soft_expiration_date NUMBER(16);
ALTER TABLE horde_users ADD user_hard_expiration_date NUMBER(16);

CREATE TABLE horde_histories (
    history_id       NUMBER(16) NOT NULL,
    object_uid       VARCHAR2(255) NOT NULL,
    history_action   VARCHAR2(32) NOT NULL,
    history_ts       NUMBER(16) NOT NULL,
    history_desc     CLOB,
    history_who      VARCHAR2(255),
    history_extra    CLOB,

    PRIMARY KEY (history_id)
);

CREATE INDEX history_action_idx ON horde_histories (history_action);
CREATE INDEX history_ts_idx ON horde_histories (history_ts);
CREATE INDEX history_uid_idx ON horde_histories (object_uid);

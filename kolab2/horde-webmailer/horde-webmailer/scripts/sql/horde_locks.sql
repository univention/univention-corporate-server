--
-- $Horde: horde/scripts/sql/horde_locks.sql,v 1.1.2.5 2008-07-20 14:25:23 chuck Exp $
--
CREATE TABLE horde_locks (
    lock_id                  VARCHAR(36) NOT NULL,
    lock_owner               VARCHAR(32) NOT NULL,
    lock_scope               VARCHAR(32) NOT NULL,
    lock_principal           VARCHAR(255) NOT NULL,
    lock_origin_timestamp    BIGINT NOT NULL,
    lock_update_timestamp    BIGINT NOT NULL,
    lock_expiry_timestamp    BIGINT NOT NULL,
    lock_type                SMALLINT UNSIGNED NOT NULL,

    PRIMARY KEY (lock_id)
);

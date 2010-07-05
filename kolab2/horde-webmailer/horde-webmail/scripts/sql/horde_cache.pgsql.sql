-- $Horde: horde/scripts/sql/horde_cache.pgsql.sql,v 1.1.2.1 2007-12-20 15:03:03 jan Exp $

CREATE TABLE horde_cache (
    cache_id          VARCHAR(32) NOT NULL,
    cache_timestamp   BIGINT NOT NULL,
    cache_data        TEXT,

    PRIMARY KEY  (cache_id)
);

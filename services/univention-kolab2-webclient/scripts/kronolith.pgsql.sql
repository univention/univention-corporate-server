-- $Horde: kronolith/scripts/sql/kronolith.pgsql.sql,v 1.8 2007/03/23 10:43:59 jan Exp $

CREATE TABLE kronolith_events (
    event_id VARCHAR(32) NOT NULL,
    event_uid VARCHAR(255) NOT NULL,
    calendar_id VARCHAR(255) NOT NULL,
    event_creator_id VARCHAR(255) NOT NULL,
    event_description TEXT,
    event_location TEXT,
    event_status INT DEFAULT 0,
    event_attendees TEXT,
    event_keywords TEXT,
    event_exceptions TEXT,
    event_title VARCHAR(255),
    event_category VARCHAR(80),
    event_recurtype SMALLINT DEFAULT 0,
    event_recurinterval SMALLINT,
    event_recurdays SMALLINT,
    event_recurenddate TIMESTAMP,
    event_recurcount INT,
    event_start TIMESTAMP,
    event_end TIMESTAMP,
    event_alarm INT DEFAULT 0,
    event_modified INT NOT NULL,
    event_private INT DEFAULT 0 NOT NULL,

    PRIMARY KEY (event_id)
);

CREATE INDEX kronolith_calendar_idx ON kronolith_events (calendar_id);
CREATE INDEX kronolith_uid_idx ON kronolith_events (event_uid);


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255) DEFAULT NULL,
    vfb_email      VARCHAR(255) DEFAULT '' NOT NULL,
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

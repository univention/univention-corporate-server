-- $Horde: kronolith/scripts/drivers/kronolith.sql,v 1.14 2004/03/12 03:23:44 chuck Exp $

CREATE TABLE kronolith_events (
    event_id VARCHAR(32) NOT NULL,
    calendar_id VARCHAR(255) NOT NULL,
    event_creator_id VARCHAR(255) NOT NULL,
    event_description TEXT,
    event_location TEXT,
    event_status INT DEFAULT 0,
    event_attendees TEXT,
    event_keywords TEXT,
    event_exceptions TEXT,
    event_title VARCHAR(80),
    event_category VARCHAR(80),
    event_recurtype VARCHAR(11) DEFAULT 0,
    event_recurinterval VARCHAR(11),
    event_recurdays VARCHAR(11),
    event_recurenddate DATETIME,
    event_start DATETIME,
    event_end DATETIME,
    event_alarm INT DEFAULT 0,
    event_modified INT NOT NULL,

    PRIMARY KEY (event_id)
);

CREATE INDEX kronolith_calendar_idx ON kronolith_events (calendar_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_events TO horde;


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255) DEFAULT NULL,
    vfb_email      VARCHAR(255) NOT NULL DEFAULT '',
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_storage TO horde;

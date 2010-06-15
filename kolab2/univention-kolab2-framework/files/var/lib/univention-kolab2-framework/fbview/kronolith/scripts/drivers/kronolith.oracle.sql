-- $Horde: kronolith/scripts/drivers/kronolith.oracle.sql,v 1.5 2004/03/12 03:23:44 chuck Exp $

CREATE TABLE kronolith_events (
    event_id VARCHAR2(32) NOT NULL,
    calendar_id VARCHAR2(255) NOT NULL,
    event_creator_id VARCHAR2(255) NOT NULL,
    event_description VARCHAR2(4000),
    event_location VARCHAR2(4000),
    event_status INT DEFAULT 0,
    event_attendees VARCHAR2(4000),
    event_keywords VARCHAR2(4000),
    event_exceptions VARCHAR2(4000),
    event_title VARCHAR2(80),
    event_category VARCHAR2(80),
    event_recurtype VARCHAR2(11) DEFAULT '0',
    event_recurinterval VARCHAR2(11),
    event_recurdays VARCHAR2(11),
    event_recurenddate DATE,
    event_start DATE,
    event_end DATE,
    event_alarm INT DEFAULT 0,
    event_modified INT NOT NULL,

    PRIMARY KEY (event_id)
);

CREATE INDEX kronolith_calendar_idx ON kronolith_events (calendar_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_events TO horde;


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR2(255) DEFAULT NULL,
    vfb_email      VARCHAR2(255) NOT NULL DEFAULT '',
    vfb_serialized VARCHAR2(4000) NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_storage TO horde;

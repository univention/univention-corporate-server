-- $Horde: kronolith/scripts/add_meetings.sql,v 1.2 2004/05/22 12:26:33 mdjukic Exp $

ALTER TABLE kronolith_events ADD COLUMN event_status INT DEFAULT 0 AFTER event_location;
ALTER TABLE kronolith_events ADD COLUMN event_attendees TEXT AFTER event_status;


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255) DEFAULT NULL,
    vfb_email      VARCHAR(255) NOT NULL DEFAULT '',
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_storage TO horde;

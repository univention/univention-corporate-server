-- $Horde: kronolith/scripts/add_meetings_psql.sql,v 1.1 2004/03/12 03:23:43 chuck Exp $

ALTER TABLE kronolith_events ADD COLUMN event_status INT;
ALTER TABLE kronolith_events ALTER COLUMN event_status SET DEFAULT 0;
ALTER TABLE kronolith_events ADD COLUMN event_attendees TEXT;


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255) DEFAULT NULL,
    vfb_email      VARCHAR(255) NOT NULL DEFAULT '',
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

GRANT SELECT, INSERT, UPDATE, DELETE ON kronolith_storage TO horde;

-- $Horde: kronolith/scripts/upgrades/1.1_to_2.0.mysql.sql,v 1.4.2.2 2009-10-22 16:48:56 jan Exp $
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ mysql --user=root --password=<MySQL-root-password> <db name> < 1.1_to_2.0.mysql.sql

ALTER TABLE kronolith_events CHANGE COLUMN event_id event_id VARCHAR(32) NOT NULL;
ALTER TABLE kronolith_events CHANGE COLUMN event_title event_title VARCHAR(255);

ALTER TABLE kronolith_events ADD COLUMN event_uid VARCHAR(255) NOT NULL;
ALTER TABLE kronolith_events ADD COLUMN event_creator_id VARCHAR(255) NOT NULL;
ALTER TABLE kronolith_events ADD COLUMN event_status INT DEFAULT 0;
ALTER TABLE kronolith_events ADD COLUMN event_attendees TEXT;

CREATE INDEX kronolith_uid_idx ON kronolith_events (event_uid);


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255),
    vfb_email      VARCHAR(255) NOT NULL,
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

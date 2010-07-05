-- $Horde: kronolith/scripts/upgrades/1.1_to_2.0.pgsql.sql,v 1.1.2.4 2009-10-22 16:48:56 jan Exp $
--
-- Update script to update Kronolith 1.1 data to 2.x data for pgsql
-- Converted from mysql version by Daniel E. Markle <lexicon@seul.org>
--
-- You can simply execute this file in your database.
--
-- Run as:
--
-- $ psql <db name> -f < 1.1_to_2.0.pgsql.sql

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_id_new VARCHAR(32);
UPDATE kronolith_events SET event_id_new = event_id;
ALTER TABLE kronolith_events DROP event_id;
ALTER TABLE kronolith_events RENAME event_id_new TO event_id;
ALTER TABLE kronolith_events ALTER COLUMN event_id SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_title_new VARCHAR(255);
UPDATE kronolith_events SET event_title_new = event_title;
ALTER TABLE kronolith_events DROP event_title;
ALTER TABLE kronolith_events RENAME event_title_new TO event_title;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_uid VARCHAR(255);
UPDATE kronolith_events SET event_uid = '';
ALTER TABLE kronolith_events ALTER COLUMN event_uid SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_creator_id VARCHAR(255);
UPDATE kronolith_events SET event_creator_id = '';
ALTER TABLE kronolith_events ALTER COLUMN event_creator_id SET NOT NULL;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_status INT;
UPDATE kronolith_events SET event_status = 0;
ALTER TABLE kronolith_events ALTER COLUMN event_status SET DEFAULT 0;
COMMIT;

ALTER TABLE kronolith_events ADD COLUMN event_attendees TEXT;

CREATE INDEX kronolith_uid_idx ON kronolith_events (event_uid);

CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR(255),
    vfb_email      VARCHAR(255) NOT NULL,
    vfb_serialized TEXT NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

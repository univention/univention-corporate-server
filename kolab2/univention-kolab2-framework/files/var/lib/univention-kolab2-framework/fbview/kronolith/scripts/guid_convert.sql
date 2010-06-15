-- More generic script for converting event_id to a 32-character
-- string (see guid_convert_mysql.sql for MySQL; it's much
-- simpler). This general process worked for me on Postgres.

ALTER TABLE kronolith_events ADD COLUMN new_id VARCHAR(32);
UPDATE kronolith_events SET new_id = event_id;
ALTER TABLE kronolith_events DROP COLUMN event_id;
ALTER TABLE kronolith_events RENAME COLUMN new_id TO event_id;
ALTER TABLE kronolith_events ALTER COLUMN event_id SET NOT NULL;
CREATE INDEX kronolith_events_pkey ON kronolith_events (event_id);

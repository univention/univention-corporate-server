-- MySQL script for converting event_id to a 32-character string.

ALTER TABLE kronolith_events CHANGE COLUMN event_id event_id VARCHAR(32) NOT NULL;

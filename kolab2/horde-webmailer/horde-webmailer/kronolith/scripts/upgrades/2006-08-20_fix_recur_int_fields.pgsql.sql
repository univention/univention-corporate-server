BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_recurtype_new SMALLINT DEFAULT 0;
UPDATE kronolith_events SET event_recurtype_new = CAST (event_recurtype AS SMALLINT);
ALTER TABLE kronolith_events DROP event_recurtype;
ALTER TABLE kronolith_events RENAME event_recurtype_new TO event_recurtype;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_recurinterval_new SMALLINT;
UPDATE kronolith_events SET event_recurinterval_new = CAST (event_recurinterval AS SMALLINT);
ALTER TABLE kronolith_events DROP event_recurinterval;
ALTER TABLE kronolith_events RENAME event_recurinterval_new TO event_recurinterval;
COMMIT;

BEGIN;
ALTER TABLE kronolith_events ADD COLUMN event_recurdays_new SMALLINT;
UPDATE kronolith_events SET event_recurdays_new = CAST (event_recurdays AS SMALLINT);
ALTER TABLE kronolith_events DROP event_recurdays;
ALTER TABLE kronolith_events RENAME event_recurdays_new TO event_recurdays;
COMMIT;

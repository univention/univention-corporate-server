ALTER TABLE kronolith_events CHANGE event_recurtype event_recurtype SMALLINT DEFAULT 0;
ALTER TABLE kronolith_events CHANGE event_recurinterval event_recurinterval SMALLINT;
ALTER TABLE kronolith_events CHANGE event_recurdays event_recurdays SMALLINT;

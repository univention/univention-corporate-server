-- $Horde: kronolith/scripts/upgrades/1.1_to_2.0.oci8.sql,v 1.1.2.4 2009-10-22 16:48:56 jan Exp $

ALTER TABLE kronolith_events ADD COLUMN event_id_new VARCHAR2(32);
UPDATE kronolith_events SET event_id_new = event_id;
ALTER TABLE kronolith_events DROP COLUMN event_id;
ALTER TABLE kronolith_events RENAME COLUMN event_id_new to event_id;
ALTER TABLE kronolith_events ADD CONSTRAINT event_id PRIMARY KEY (event_id);
ALTER TABLE kronolith_events MODIFY event_title VARCHAR2(255);

ALTER TABLE kronolith_events ADD event_uid VARCHAR2(255);
ALTER TABLE kronolith_events ADD event_creator_id VARCHAR2(255);
ALTER TABLE kronolith_events ADD event_status NUMBER(2) DEFAULT 0;
ALTER TABLE kronolith_events ADD event_attendees VARCHAR2(4000);

CREATE INDEX kronolith_uid_idx ON kronolith_events (event_uid);


CREATE TABLE kronolith_storage (
    vfb_owner      VARCHAR2(255),
    vfb_email      VARCHAR2(255) NOT NULL,
    vfb_serialized VARCHAR2(4000) NOT NULL
);

CREATE INDEX kronolith_vfb_owner_idx ON kronolith_storage (vfb_owner);
CREATE INDEX kronolith_vfb_email_idx ON kronolith_storage (vfb_email);

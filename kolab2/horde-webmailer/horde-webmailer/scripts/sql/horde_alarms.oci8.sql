--
-- Table structure for table horde_alarms
--
-- $Horde: horde/scripts/sql/horde_alarms.oci8.sql,v 1.7.2.2 2009-10-19 10:54:32 jan Exp $
--

CREATE TABLE horde_alarms (
    alarm_id        VARCHAR2(255) NOT NULL,
    alarm_uid       VARCHAR2(255),
    alarm_start     DATE NOT NULL,
    alarm_end       DATE,
    alarm_methods   VARCHAR2(255),
    alarm_params    CLOB,
    alarm_title     VARCHAR2(255) NOT NULL,
    alarm_text      CLOB,
    alarm_snooze    DATE,
    alarm_dismissed NUMBER(1) DEFAULT 0 NOT NULL,
    alarm_internal  CLOB
);

CREATE INDEX alarm_id_idx ON horde_alarms (alarm_id);
CREATE INDEX alarm_start_idx ON horde_alarms (alarm_start);
CREATE INDEX alarm_end_idx ON horde_alarms (alarm_end);
CREATE INDEX alarm_snooze_idx ON horde_alarms (alarm_snooze);
CREATE INDEX alarm_dismissed_idx ON horde_alarms (alarm_dismissed);

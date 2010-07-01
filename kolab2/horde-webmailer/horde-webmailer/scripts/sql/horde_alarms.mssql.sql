--
-- Table structure for table horde_alarms
--
-- $Horde: horde/scripts/sql/horde_alarms.mssql.sql,v 1.6.2.1 2007-12-20 15:03:03 jan Exp $
--

CREATE TABLE horde_alarms (
    alarm_id        VARCHAR(255) NOT NULL,
    alarm_uid       VARCHAR(255),
    alarm_start     DATETIME NOT NULL,
    alarm_end       DATETIME,
    alarm_methods   VARCHAR(255),
    alarm_params    VARCHAR(MAX),
    alarm_title     VARCHAR(255) NOT NULL,
    alarm_text      VARCHAR(MAX),
    alarm_snooze    DATETIME,
    alarm_dismissed SMALLINT DEFAULT 0 NOT NULL,
    alarm_internal  VARCHAR(MAX)
);

CREATE INDEX alarm_id_idx ON horde_alarms (alarm_id);
CREATE INDEX alarm_user_idx ON horde_alarms (alarm_uid);
CREATE INDEX alarm_start_idx ON horde_alarms (alarm_start);
CREATE INDEX alarm_end_idx ON horde_alarms (alarm_end);
CREATE INDEX alarm_snooze_idx ON horde_alarms (alarm_snooze);
CREATE INDEX alarm_dismissed_idx ON horde_alarms (alarm_dismissed);

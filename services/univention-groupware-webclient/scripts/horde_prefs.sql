-- $Horde: horde/scripts/sql/horde_prefs.sql,v 1.2 2004/09/21 03:34:06 chuck Exp $

CREATE TABLE horde_prefs (
    pref_uid        VARCHAR(255) NOT NULL,
    pref_scope      VARCHAR(16) NOT NULL DEFAULT '',
    pref_name       VARCHAR(32) NOT NULL,
    pref_value      TEXT,
--
    PRIMARY KEY (pref_uid, pref_scope, pref_name)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_prefs TO horde;

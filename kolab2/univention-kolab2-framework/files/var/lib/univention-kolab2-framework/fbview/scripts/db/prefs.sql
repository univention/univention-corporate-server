-- $Horde: horde/scripts/db/prefs.sql,v 1.8 2003/07/14 16:33:08 mdjukic Exp $

CREATE TABLE horde_prefs (
    pref_uid        VARCHAR(255) NOT NULL,
    pref_scope      VARCHAR(16) NOT NULL DEFAULT '',
    pref_name       VARCHAR(32) NOT NULL,
    pref_value      TEXT,

    PRIMARY KEY (pref_uid, pref_scope, pref_name)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON horde_prefs TO horde;

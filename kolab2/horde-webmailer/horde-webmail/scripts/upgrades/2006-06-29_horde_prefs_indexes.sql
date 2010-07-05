-- This script adds additional indexes to the horde_prefs table that should
-- improve loading of preferences from the preference table.
--
-- $Horde: horde/scripts/upgrades/2006-06-29_horde_prefs_indexes.sql,v 1.1.2.2 2007-12-20 15:03:04 jan Exp $

CREATE INDEX pref_uid_idx ON horde_prefs (pref_uid);
CREATE INDEX pref_scope_idx ON horde_prefs (pref_scope);


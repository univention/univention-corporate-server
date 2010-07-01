-- Use this script to convert CHAR columns in horde_prefs to VARCHAR2 and trim
-- the space padding.  This is only necessary if horde_prefs was created using
-- scripts/sql/create.oci8.sql
--
-- $Horde: horde/scripts/upgrades/2005-09-22_horde_prefs_varchar2.oci8.sql,v 1.1.2.2 2007-12-20 15:03:04 jan Exp $
--
ALTER TABLE horde_prefs MODIFY pref_uid VARCHAR2(255);
ALTER TABLE horde_prefs MODIFY pref_scope VARCHAR2(16);
ALTER TABLE horde_prefs MODIFY pref_name VARCHAR2(32);
UPDATE horde_prefs SET pref_uid = RTRIM(pref_uid);
UPDATE horde_prefs SET pref_scope = RTRIM(pref_scope);
UPDATE horde_prefs SET pref_name = RTRIM(pref_name);

-- $Horde: turba/scripts/upgrades/1.2_to_2.0.oci8.sql,v 1.1.2.3 2009-10-19 10:54:38 jan Exp $

ALTER TABLE turba_objects ADD object_uid VARCHAR2(255);
ALTER TABLE turba_objects ADD object_freebusyurl VARCHAR2(255);
ALTER TABLE turba_objects ADD object_smimepublickey CLOB;
ALTER TABLE turba_objects ADD object_pgppublickey CLOB;

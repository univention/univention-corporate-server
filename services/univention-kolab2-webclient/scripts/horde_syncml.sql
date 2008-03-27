--
-- $Horde: horde/scripts/sql/horde_syncml.sql,v 1.4.2.1 2007/12/20 15:03:03 jan Exp $
--

CREATE TABLE horde_syncml_map (
    syncml_syncpartner VARCHAR(64) NOT NULL,
    syncml_db          VARCHAR(64) NOT NULL,
    syncml_uid         VARCHAR(64) NOT NULL,
    syncml_cuid        VARCHAR(64),
    syncml_suid        VARCHAR(64),
    syncml_timestamp   INTEGER
);

CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_syncpartner, syncml_db, syncml_uid, syncml_cuid);
CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_syncpartner, syncml_db, syncml_uid, syncml_suid);


-- delete old map entries from datatree
DELETE FROM horde_datatree WHERE group_uid = 'syncml';

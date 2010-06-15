-- $Horde: horde/scripts/db/muvfs.sql,v 1.2 2002/09/02 10:39:06 jan Exp $

CREATE TABLE horde_muvfs (
    vfs_id        BIGINT NOT NULL,
    vfs_type      SMALLINT NOT NULL,
    vfs_path      VARCHAR(255) NOT NULL,
    vfs_name      VARCHAR(255) NOT NULL,
    vfs_modified  BIGINT NOT NULL,
    vfs_owner     VARCHAR(255) NOT NULL,
    vfs_perms     SMALLINT NOT NULL,
    vfs_data      LONGBLOB,
-- Or, on some DBMS systems:
--  vfs_data      IMAGE,
    PRIMARY KEY   (vfs_id)
);

CREATE INDEX vfs_path_idx ON horde_muvfs (vfs_path);
CREATE INDEX vfs_name_idx ON horde_muvfs (vfs_name);

-- $Horde: turba/scripts/drivers/wedding.sql,v 1.2 2003/04/27 00:28:07 chuck Exp $

CREATE TABLE turba_weddingguests (
    object_id              VARCHAR(32) NOT NULL DEFAULT '',
    owner_id               VARCHAR(255) NOT NULL DEFAULT '',
    object_type            VARCHAR(255) NOT NULL DEFAULT 'Object',
    object_members         BLOB,
    object_name1           VARCHAR(255) DEFAULT NULL,
    object_email1          VARCHAR(255) DEFAULT NULL,
    object_homeaddress     VARCHAR(255) DEFAULT NULL,
    object_homephone       VARCHAR(25) DEFAULT NULL,
    object_meal1           VARCHAR(50) DEFAULT NULL,
    object_table           VARCHAR(50) DEFAULT NULL,
    object_rsvp            VARCHAR(50) DEFAULT NULL,
    object_brunch_rsvp     VARCHAR(50) DEFAULT NULL,
    object_gift            VARCHAR(100) DEFAULT NULL,
    object_thankyou        VARCHAR(50) DEFAULT NULL,
    object_notes           TEXT,
    object_meal2           VARCHAR(50) DEFAULT NULL,
    object_name2           VARCHAR(255) DEFAULT NULL,
    object_email2          VARCHAR(255) DEFAULT NULL,
    object_brunch_invited  VARCHAR(10) DEFAULT NULL,

    PRIMARY KEY (object_id)
);

CREATE INDEX turba_wedding_idx ON turba_weddingguests (owner_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON turba_weddingguests TO horde;

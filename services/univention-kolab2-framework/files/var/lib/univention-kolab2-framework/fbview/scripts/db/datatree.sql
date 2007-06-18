-- $Horde: horde/scripts/db/datatree.sql,v 1.1 2004/03/18 20:25:10 jan Exp $

CREATE TABLE horde_datatree (
    datatree_id INT NOT NULL,
    group_uid VARCHAR(255) NOT NULL,
    user_uid VARCHAR(255) NOT NULL,
    datatree_name VARCHAR(255) NOT NULL,
    datatree_parents VARCHAR(255) NOT NULL,
    datatree_order INT,
-- There is no portable way to do this apparently. If your db doesn't allow varchars
-- greater than 255 characters, then maybe it allows TEXT columns, so try the second
-- line.
    datatree_data VARCHAR(2048),
--  datatree_data TEXT,
    datatree_serialized SMALLINT DEFAULT 0 NOT NULL,
    datatree_updated TIMESTAMP,

    PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_order_idx ON horde_datatree (datatree_order);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);


CREATE TABLE horde_datatree_attributes (
    datatree_id INT NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_key VARCHAR(255),
    attribute_value TEXT
);

CREATE INDEX datatree_attribute_idx ON horde_datatree_attributes (datatree_id);
CREATE INDEX datatree_attribute_name_idx ON horde_datatree_attributes (attribute_name);
CREATE INDEX datatree_attribute_key_idx ON horde_datatree_attributes (attribute_key);


GRANT SELECT, INSERT, UPDATE, DELETE ON horde_datatree TO horde;
GRANT SELECT, INSERT, UPDATE, DELETE ON horde_datatree_attributes TO horde;

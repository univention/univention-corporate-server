-- $Horde: horde/scripts/sql/horde_datatree.mysql.sql,v 1.1.10.2 2007-12-20 15:03:03 jan Exp $

CREATE TABLE horde_datatree (
       datatree_id INT NOT NULL,
       group_uid VARCHAR(255) NOT NULL,
       user_uid VARCHAR(255) NOT NULL,
       datatree_name VARCHAR(255) NOT NULL,
       datatree_parents VARCHAR(255) NOT NULL,
       datatree_order INT,
       datatree_data TEXT,
       datatree_serialized SMALLINT DEFAULT 0 NOT NULL,
       PRIMARY KEY (datatree_id)
);

CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name);
CREATE INDEX datatree_group_idx ON horde_datatree (group_uid);
CREATE INDEX datatree_user_idx ON horde_datatree (user_uid);
CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized);
CREATE INDEX datatree_parents_idx ON horde_datatree (datatree_parents);

CREATE TABLE horde_datatree_attributes (
    datatree_id INT NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_key VARCHAR(255) DEFAULT '' NOT NULL,
    attribute_value TEXT
);

CREATE INDEX datatree_attribute_idx ON horde_datatree_attributes (datatree_id);
CREATE INDEX datatree_attribute_name_idx ON horde_datatree_attributes (attribute_name);
CREATE INDEX datatree_attribute_key_idx ON horde_datatree_attributes (attribute_key);
CREATE INDEX datatree_attribute_value_idx ON horde_datatree_attributes (attribute_value(255));

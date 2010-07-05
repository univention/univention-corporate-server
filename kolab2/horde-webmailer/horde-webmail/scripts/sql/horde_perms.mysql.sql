CREATE TABLE horde_perms (
    perm_id INT(11) NOT NULL,
    perm_name VARCHAR(255) NOT NULL,
    perm_parents VARCHAR(255) NOT NULL,
    perm_data TEXT,
    PRIMARY KEY (perm_id),
    UNIQUE KEY perm_name (perm_name)
);

CREATE TABLE horde_perms (
    perm_id NUMBER(16) NOT NULL,
    perm_name VARCHAR2(255) NOT NULL UNIQUE,
    perm_parents VARCHAR2(255) NOT NULL,
    perm_data CLOB,
    PRIMARY KEY (perm_id)
);

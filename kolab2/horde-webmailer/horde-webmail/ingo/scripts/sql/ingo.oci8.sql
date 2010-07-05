-- $Horde: ingo/scripts/sql/ingo.oci8.sql,v 1.3.2.10 2009-10-20 21:44:32 jan Exp $

CREATE TABLE ingo_rules (
    rule_id NUMBER(16) NOT NULL,
    rule_owner VARCHAR2(255) NOT NULL,
    rule_name VARCHAR2(255) NOT NULL,
    rule_action NUMBER(16) NOT NULL,
    rule_value VARCHAR2(255),
    rule_flags NUMBER(16),
    rule_conditions CLOB,
    rule_combine NUMBER(16),
    rule_stop NUMBER(1),
    rule_active NUMBER(1) DEFAULT 1 NOT NULL,
    rule_order NUMBER(16) DEFAULT 0 NOT NULL,
--
    PRIMARY KEY (rule_id)
);

CREATE INDEX rule_owner_idx ON ingo_rules (rule_owner);


CREATE TABLE ingo_lists (
    list_owner VARCHAR2(255) NOT NULL,
    list_blacklist NUMBER(1) DEFAULT 0,
    list_address VARCHAR2(255) NOT NULL
);

CREATE INDEX list_idx ON ingo_lists (list_owner, list_blacklist);


CREATE TABLE ingo_forwards (
    forward_owner VARCHAR2(255) NOT NULL,
    forward_addresses CLOB,
    forward_keep NUMBER(16) DEFAULT 0 NOT NULL,
--
    PRIMARY KEY (forward_owner)
);


CREATE TABLE ingo_vacations (
    vacation_owner VARCHAR2(255) NOT NULL,
    vacation_addresses CLOB,
    vacation_subject VARCHAR2(255),
    vacation_reason CLOB,
    vacation_days NUMBER(16) DEFAULT 7,
    vacation_start NUMBER(16),
    vacation_end NUMBER(16),
    vacation_excludes CLOB,
    vacation_ignorelists NUMBER(1) DEFAULT 1,
--
    PRIMARY KEY (vacation_owner)
);


CREATE TABLE ingo_spam (
    spam_owner VARCHAR2(255) NOT NULL,
    spam_level NUMBER(16) DEFAULT 5,
    spam_folder VARCHAR2(255),
--
    PRIMARY KEY (spam_owner)
);


CREATE TABLE ingo_shares (
    share_id NUMBER(16) NOT NULL,
    share_name VARCHAR2(255) NOT NULL,
    share_owner VARCHAR2(255) NOT NULL,
    share_flags NUMBER(8) DEFAULT 0 NOT NULL,
    perm_creator NUMBER(8) DEFAULT 0 NOT NULL,
    perm_default NUMBER(8) DEFAULT 0 NOT NULL,
    perm_guest NUMBER(8) DEFAULT 0 NOT NULL,
    attribute_name VARCHAR2(255) NOT NULL,
    attribute_desc VARCHAR2(255),
    PRIMARY KEY (share_id)
);

CREATE INDEX ingo_shares_name_idx ON ingo_shares (share_name);
CREATE INDEX ingo_shares_owner_idx ON ingo_shares (share_owner);
CREATE INDEX ingo_shares_creator_idx ON ingo_shares (perm_creator);
CREATE INDEX ingo_shares_default_idx ON ingo_shares (perm_default);
CREATE INDEX ingo_shares_guest_idx ON ingo_shares (perm_guest);

CREATE TABLE ingo_shares_groups (
    share_id NUMBER(16) NOT NULL,
    group_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX ingo_groups_share_id_idx ON ingo_shares_groups (share_id);
CREATE INDEX ingo_groups_group_uid_idx ON ingo_shares_groups (group_uid);
CREATE INDEX ingo_groups_perm_idx ON ingo_shares_groups (perm);

CREATE TABLE ingo_shares_users (
    share_id NUMBER(16) NOT NULL,
    user_uid VARCHAR2(255) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX ingo_users_share_id_idx ON ingo_shares_users (share_id);
CREATE INDEX ingo_users_user_uid_idx ON ingo_shares_users (user_uid);
CREATE INDEX ingo_users_perm_idx ON ingo_shares_users (perm);

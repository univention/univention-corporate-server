-- $Horde: turba/scripts/upgrades/2.1_to_2.2_add_sql_share_tables.oci8.sql,v 1.1.2.5 2009-10-20 21:44:34 jan Exp $

CREATE TABLE turba_shares (
    share_id NUMBER(16) NOT NULL,
    share_name VARCHAR2(255) NOT NULL,
    share_owner VARCHAR2(32) NOT NULL,
    share_flags NUMBER(8) DEFAULT 0 NOT NULL,
    perm_creator NUMBER(8) DEFAULT 0 NOT NULL,
    perm_default NUMBER(8) DEFAULT 0 NOT NULL,
    perm_guest NUMBER(8) DEFAULT 0 NOT NULL,
    attribute_name VARCHAR2(255) NOT NULL,
    attribute_desc VARCHAR2(255),
    attribute_params VARCHAR2(4000),
    PRIMARY KEY (share_id)
);

CREATE INDEX turba_shares_name_idx ON turba_shares (share_name);
CREATE INDEX turba_shares_owner_idx ON turba_shares (share_owner);
CREATE INDEX turba_shares_creator_idx ON turba_shares (perm_creator);
CREATE INDEX turba_shares_default_idx ON turba_shares (perm_default);
CREATE INDEX turba_shares_guest_idx ON turba_shares (perm_guest);

CREATE TABLE turba_shares_groups (
    share_id NUMBER(16) NOT NULL,
    group_uid NUMBER(16) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX turba_groups_share_id_idx ON turba_shares_groups (share_id);
CREATE INDEX turba_groups_group_uid_idx ON turba_shares_groups (group_uid);
CREATE INDEX turba_groups_perm_idx ON turba_shares_groups (perm);

CREATE TABLE turba_shares_users (
    share_id NUMBER(16) NOT NULL,
    user_uid VARCHAR2(32) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX turba_users_share_id_idx ON turba_shares_users (share_id);
CREATE INDEX turba_users_user_uid_idx ON turba_shares_users (user_uid);
CREATE INDEX turba_users_perm_idx ON turba_shares_users (perm);

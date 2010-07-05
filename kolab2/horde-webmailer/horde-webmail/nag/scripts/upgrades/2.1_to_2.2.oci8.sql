ALTER TABLE nag_tasks ADD task_estimate FLOAT;
ALTER TABLE nag_tasks ADD task_completed_date NUMBER(16);
ALTER TABLE nag_tasks ADD task_start NUMBER(16);
ALTER TABLE nag_tasks ADD task_parent VARCHAR2(32);

CREATE INDEX nag_start_idx ON nag_tasks (task_start);

CREATE TABLE nag_shares (
    share_id NUMBER(16) NOT NULL,
    share_name VARCHAR2(255) NOT NULL,
    share_owner VARCHAR2(32) NOT NULL,
    share_flags NUMBER(8) DEFAULT 0 NOT NULL,
    perm_creator NUMBER(8) DEFAULT 0 NOT NULL,
    perm_default NUMBER(8) DEFAULT 0 NOT NULL,
    perm_guest NUMBER(8) DEFAULT 0 NOT NULL,
    attribute_name VARCHAR2(255) NOT NULL,
    attribute_desc VARCHAR2(255),
    PRIMARY KEY (share_id)
);

CREATE INDEX nag_shares_name_idx ON nag_shares (share_name);
CREATE INDEX nag_shares_owner_idx ON nag_shares (share_owner);
CREATE INDEX nag_shares_creator_idx ON nag_shares (perm_creator);
CREATE INDEX nag_shares_default_idx ON nag_shares (perm_default);
CREATE INDEX nag_shares_guest_idx ON nag_shares (perm_guest);

CREATE TABLE nag_shares_groups (
    share_id NUMBER(16) NOT NULL,
    group_uid NUMBER(16) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX nag_groups_share_id_idx ON nag_shares_groups (share_id);
CREATE INDEX nag_groups_group_uid_idx ON nag_shares_groups (group_uid);
CREATE INDEX nag_groups_perm_idx ON nag_shares_groups (perm);

CREATE TABLE nag_shares_users (
    share_id NUMBER(16) NOT NULL,
    user_uid VARCHAR2(32) NOT NULL,
    perm NUMBER(8) NOT NULL
);

CREATE INDEX nag_users_share_id_idx ON nag_shares_users (share_id);
CREATE INDEX nag_users_user_uid_idx ON nag_shares_users (user_uid);
CREATE INDEX nag_users_perm_idx ON nag_shares_users (perm);

-- $Horde: nag/scripts/sql/nag.sql,v 1.4.8.10 2009-10-22 14:24:20 jan Exp $

CREATE TABLE nag_tasks (
    task_id              VARCHAR(32) NOT NULL,
    task_owner           VARCHAR(255) NOT NULL,
    task_creator         VARCHAR(255) NOT NULL,
    task_parent          VARCHAR(255),
    task_assignee        VARCHAR(255),
    task_name            VARCHAR(255) NOT NULL,
    task_uid             VARCHAR(255) NOT NULL,
    task_desc            TEXT,
    task_start           INT,
    task_due             INT,
    task_priority        INT DEFAULT 0 NOT NULL,
    task_estimate        FLOAT,
    task_category        VARCHAR(80),
    task_completed       SMALLINT DEFAULT 0 NOT NULL,
    task_completed_date  INT,
    task_alarm           INT DEFAULT 0 NOT NULL,
    task_private         SMALLINT DEFAULT 0 NOT NULL,
--
    PRIMARY KEY (task_id)
);

CREATE INDEX nag_tasklist_idx ON nag_tasks (task_owner);
CREATE INDEX nag_uid_idx ON nag_tasks (task_uid);
CREATE INDEX nag_start_idx ON nag_tasks (task_start);

CREATE TABLE nag_shares (
    share_id INT NOT NULL,
    share_name VARCHAR(255) NOT NULL,
    share_owner VARCHAR(255) NOT NULL,
    share_flags SMALLINT DEFAULT 0 NOT NULL,
    perm_creator SMALLINT DEFAULT 0 NOT NULL,
    perm_default SMALLINT DEFAULT 0 NOT NULL,
    perm_guest SMALLINT DEFAULT 0 NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    attribute_desc VARCHAR(255),
    PRIMARY KEY (share_id)
);

CREATE INDEX nag_shares_share_name_idx ON nag_shares (share_name);
CREATE INDEX nag_shares_share_owner_idx ON nag_shares (share_owner);
CREATE INDEX nag_shares_perm_creator_idx ON nag_shares (perm_creator);
CREATE INDEX nag_shares_perm_default_idx ON nag_shares (perm_default);
CREATE INDEX nag_shares_perm_guest_idx ON nag_shares (perm_guest);

CREATE TABLE nag_shares_groups (
    share_id INT NOT NULL,
    group_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX nag_shares_groups_share_id_idx ON nag_shares_groups (share_id);
CREATE INDEX nag_shares_groups_group_uid_idx ON nag_shares_groups (group_uid);
CREATE INDEX nag_shares_groups_perm_idx ON nag_shares_groups (perm);

CREATE TABLE nag_shares_users (
    share_id INT NOT NULL,
    user_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX nag_shares_users_share_id_idx ON nag_shares_users (share_id);
CREATE INDEX nag_shares_users_user_uid_idx ON nag_shares_users (user_uid);
CREATE INDEX nag_shares_users_perm_idx ON nag_shares_users (perm);

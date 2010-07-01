-- $Horde: mnemo/scripts/sql/mnemo.sql,v 1.5.2.8 2009-10-20 21:44:35 jan Exp $

CREATE TABLE mnemo_memos (
    memo_owner      VARCHAR(255) NOT NULL,
    memo_id         VARCHAR(32) NOT NULL,
    memo_uid        VARCHAR(255) NOT NULL,
    memo_desc       VARCHAR(64) NOT NULL,
    memo_body       TEXT,
    memo_category   VARCHAR(80),
    memo_private    SMALLINT DEFAULT 0 NOT NULL,
--
    PRIMARY KEY (memo_owner, memo_id)
);

CREATE INDEX mnemo_notepad_idx ON mnemo_memos (memo_owner);
CREATE INDEX mnemo_uid_idx ON mnemo_memos (memo_uid);

CREATE TABLE mnemo_shares (
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

CREATE INDEX mnemo_shares_share_name_idx ON mnemo_shares (share_name);
CREATE INDEX mnemo_shares_share_owner_idx ON mnemo_shares (share_owner);
CREATE INDEX mnemo_shares_perm_creator_idx ON mnemo_shares (perm_creator);
CREATE INDEX mnemo_shares_perm_default_idx ON mnemo_shares (perm_default);
CREATE INDEX mnemo_shares_perm_guest_idx ON mnemo_shares (perm_guest);

CREATE TABLE mnemo_shares_groups (
    share_id INT NOT NULL,
    group_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX mnemo_shares_groups_share_id_idx ON mnemo_shares_groups (share_id);
CREATE INDEX mnemo_shares_groups_group_uid_idx ON mnemo_shares_groups (group_uid);
CREATE INDEX mnemo_shares_groups_perm_idx ON mnemo_shares_groups (perm);

CREATE TABLE mnemo_shares_users (
    share_id INT NOT NULL,
    user_uid VARCHAR(255) NOT NULL,
    perm SMALLINT NOT NULL
);

CREATE INDEX mnemo_shares_users_share_id_idx ON mnemo_shares_users (share_id);
CREATE INDEX mnemo_shares_users_user_uid_idx ON mnemo_shares_users (user_uid);
CREATE INDEX mnemo_shares_users_perm_idx ON mnemo_shares_users (perm);

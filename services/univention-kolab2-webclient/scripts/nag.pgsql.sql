-- $Horde: nag/scripts/sql/nag.sql,v 1.13 2007/06/09 12:54:34 chuck Exp $

CREATE TABLE nag_tasks (
    task_id              VARCHAR(32) NOT NULL,
    task_owner           VARCHAR(255) NOT NULL,
    task_creator         VARCHAR(255) NOT NULL,
    task_parent          VARCHAR(32) NOT NULL,
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

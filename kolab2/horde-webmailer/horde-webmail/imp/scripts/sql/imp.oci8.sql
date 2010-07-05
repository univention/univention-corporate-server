CREATE TABLE imp_sentmail (
    sentmail_id        NUMBER(16) NOT NULL,
    sentmail_who       VARCHAR2(255) NOT NULL,
    sentmail_ts        NUMBER(16) NOT NULL,
    sentmail_messageid VARCHAR2(255) NOT NULL,
    sentmail_action    VARCHAR2(32) NOT NULL,
    sentmail_recipient VARCHAR2(255) NOT NULL,
    sentmail_success   NUMBER(1) NOT NULL,
--
    PRIMARY KEY (sentmail_id)
);

CREATE INDEX sentmail_ts_idx ON imp_sentmail (sentmail_ts);
CREATE INDEX sentmail_who_idx ON imp_sentmail (sentmail_who);
CREATE INDEX sentmail_success_idx ON imp_sentmail (sentmail_success);

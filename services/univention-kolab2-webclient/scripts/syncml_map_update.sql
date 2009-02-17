
alter table horde_syncml_map add column syncml_syncpartner2 varchar(255);
update horde_syncml_map set syncml_syncpartner2=syncml_syncpartner;
alter table horde_syncml_map drop column syncml_syncpartner;
alter table horde_syncml_map rename column syncml_syncpartner2 TO syncml_syncpartner;

alter table horde_syncml_map add column syncml_db2 varchar(255);
update horde_syncml_map set syncml_db2=syncml_db;
alter table horde_syncml_map drop column syncml_db;
alter table horde_syncml_map rename column syncml_db2 TO syncml_db;

alter table horde_syncml_map add column syncml_uid2 varchar(255);
update horde_syncml_map set syncml_uid2=syncml_uid;
alter table horde_syncml_map drop column syncml_uid;
alter table horde_syncml_map rename column syncml_uid2 TO syncml_uid;

alter table horde_syncml_map add column syncml_cuid2 varchar(255);
update horde_syncml_map set syncml_cuid2=syncml_cuid;
alter table horde_syncml_map drop column syncml_cuid;
alter table horde_syncml_map rename column syncml_cuid2 TO syncml_cuid;

alter table horde_syncml_map add column syncml_suid2 varchar(255);
update horde_syncml_map set syncml_suid2=syncml_suid;
alter table horde_syncml_map drop column syncml_suid;
alter table horde_syncml_map rename column syncml_suid2 TO syncml_suid;

alter table horde_syncml_map add column syncml_timestamp2 BIGINT;
update horde_syncml_map set syncml_timestamp2=syncml_timestamp;
alter table horde_syncml_map drop column syncml_timestamp;
alter table horde_syncml_map rename column syncml_timestamp2 TO syncml_timestamp;

CREATE INDEX syncml_syncpartner_idx ON horde_syncml_map (syncml_syncpartner);
CREATE INDEX syncml_db_idx ON horde_syncml_map (syncml_db);
CREATE INDEX syncml_uid_idx ON horde_syncml_map (syncml_uid);
CREATE INDEX syncml_cuid_idx ON horde_syncml_map (syncml_cuid);
CREATE INDEX syncml_suid_idx ON horde_syncml_map (syncml_suid);


alter table horde_syncml_anchors add column syncml_syncpartner2 varchar(255);
update horde_syncml_anchors set syncml_syncpartner2=syncml_syncpartner;
alter table horde_syncml_anchors drop column syncml_syncpartner;
alter table horde_syncml_anchors rename column syncml_syncpartner2 TO syncml_syncpartner;

alter table horde_syncml_anchors add column syncml_db2 varchar(255);
update horde_syncml_anchors set syncml_db2=syncml_db;
alter table horde_syncml_anchors drop column syncml_db;
alter table horde_syncml_anchors rename column syncml_db2 TO syncml_db;

alter table horde_syncml_anchors add column syncml_uid2 varchar(255);
update horde_syncml_anchors set syncml_uid2=syncml_uid;
alter table horde_syncml_anchors drop column syncml_uid;
alter table horde_syncml_anchors rename column syncml_uid2 TO syncml_uid;

alter table horde_syncml_anchors add column syncml_clientanchor2 varchar(255);
update horde_syncml_anchors set syncml_clientanchor2=syncml_clientanchor;
alter table horde_syncml_anchors drop column syncml_clientanchor;
alter table horde_syncml_anchors rename column syncml_clientanchor2 TO syncml_clientanchor;

alter table horde_syncml_anchors add column syncml_serveranchor2 varchar(255);
update horde_syncml_anchors set syncml_serveranchor2=syncml_serveranchor;
alter table horde_syncml_anchors drop column syncml_serveranchor;
alter table horde_syncml_anchors rename column syncml_serveranchor2 TO syncml_serveranchor;

CREATE INDEX syncml_anchors_syncpartner_idx ON horde_syncml_anchors (syncml_syncpartner);
CREATE INDEX syncml_anchors_db_idx ON horde_syncml_anchors (syncml_db);
CREATE INDEX syncml_anchors_uid_idx ON horde_syncml_anchors (syncml_uid);


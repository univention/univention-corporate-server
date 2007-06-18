-- horde tables definitions : sql script

-- 01/22/2003 - F. Helly <francois.helly@wanadoo.fr>

-- command line syntax :  isql -ihorde_sybase.sql

-- warning : use nvarchar only if you need unicode encoding for some strings



use horde
go


DROP TABLE horde_datatree
go

DROP TABLE horde_prefs
go

DROP TABLE horde_users
go

DROP TABLE horde_sessionhandler
go

-- DROP TABLE horde_datatree_seq
-- go

-- DROP TABLE horde_tokens
-- go

-- DROP TABLE horde_vfs
-- go

-- DROP TABLE horde_muvfs
-- go


CREATE TABLE horde_users (
  user_uid varchar(256) NOT NULL,
  user_pass varchar(32) NOT NULL,
  PRIMARY KEY  (user_uid)
) 
go

CREATE TABLE horde_datatree (
  datatree_id numeric(11,0) IDENTITY NOT NULL,
  group_uid varchar(256) NOT NULL,
  user_uid varchar(256) NOT NULL,
  datatree_name varchar(256) NOT NULL,
  datatree_parents varchar(256) NULL,
  datatree_data text NULL,
  datatree_serialized smallint DEFAULT 0 NOT NULL,
  datatree_updated timestamp,
  PRIMARY KEY  (datatree_id),
  FOREIGN KEY (user_uid)
    REFERENCES horde_users(user_uid)
 ) 
go

CREATE TABLE horde_prefs (
  pref_uid varchar(256) NOT NULL,
  pref_scope varchar(16) NOT NULL,
  pref_name varchar(32) NOT NULL,
  pref_value text NULL,
  PRIMARY KEY  (pref_uid,pref_scope,pref_name)
)
go 

CREATE TABLE horde_sessionhandler (
  session_id varchar(32) NOT NULL,
  session_lastmodified numeric(11,0) NOT NULL,
  session_data image NULL,
  PRIMARY KEY  (session_id)
) 
go


-- CREATE TABLE horde_datatree_seq (
--   id numeric(10,0) IDENTITY NOT NULL,
--   PRIMARY KEY  (id)
-- ) 
-- go

-- CREATE TABLE horde_tokens (
--   token_address varchar(8) NOT NULL,
--   token_id varchar(32) NOT NULL,
--   token_timestamp numeric(20,0) NOT NULL,
--   PRIMARY KEY  (token_address,token_id)
-- ) 
-- go

-- CREATE TABLE horde_vfs (
--   vfs_id numeric(20,0) NOT NULL,
--   vfs_type numeric(8,0) NOT NULL,
--   vfs_path varchar(256) NOT NULL,
--   vfs_name nvarchar(256) NOT NULL,
--   vfs_modified numeric(20,0) NOT NULL,
--   vfs_owner varchar(256) NOT NULL,
--   vfs_data image NULL,
--   PRIMARY KEY  (vfs_id)
-- ) 
-- go

-- CREATE TABLE horde_muvfs (
--   vfs_id  numeric(20,0) NOT NULL,
--   vfs_type      numeric(8,0) NOT NULL,
--   vfs_path      varchar(256) NOT NULL,
--   vfs_name      varchar(256) NOT NULL,
--   vfs_modified  numeric(8,0) NOT NULL,
--   vfs_owner     varchar(256) NOT NULL,
--   vfs_perms     smallint NOT NULL,
--   vfs_data      image NULL,
--   PRIMARY KEY   (vfs_id)
--   )
-- go


CREATE INDEX datatree_datatree_name_idx ON horde_datatree (datatree_name)
go

CREATE INDEX datatree_group_idx ON horde_datatree (group_uid)
go

CREATE INDEX datatree_user_idx ON horde_datatree (user_uid)
go

CREATE INDEX datatree_serialized_idx ON horde_datatree (datatree_serialized)
go

-- CREATE INDEX vfs_path_idx ON horde_vfs (vfs_path)
-- go

-- CREATE INDEX vfs_name_idx ON horde_vfs (vfs_name)
-- go

-- CREATE INDEX vfs_path_idx ON horde_muvfs (vfs_path)
-- go

-- CREATE INDEX vfs_name_idx ON horde_muvfs (vfs_name)
-- go


grant select, insert, delete, update on editor to horde
go
grant select, insert, delete, update on host to horde
go
grant select, insert, delete, update on dbase to horde
go
grant select, insert, delete, update on site to horde
go
grant select, insert, delete, update on connection to horde
go
grant select, insert, delete, update on horde_datatree to horde
go
grant select, insert, delete, update on horde_prefs to horde
go
grant select, insert, delete, update on horde_sessionhandler to horde
go

-- grant select, insert, delete, update on horde_datatree_seq to horde
-- go
-- grant select, insert, delete, update on horde_tokens to horde
-- go
-- grant select, insert, delete, update on horde_vfs to horde
-- go
-- grant select, insert, delete, update on horde_muvfs to horde
-- go



-- add you admin_user_uid and admin_user_pass

-- insert into horde_users values ('your_admin_user_uid', 'your_admin_user_pass_md5_encrypted')
-- go

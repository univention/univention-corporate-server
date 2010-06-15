CREATE DATABASE HORDE
    CONTROLFILE REUSE
    LOGFILE  '/home/oracle/oradata/horde/redo01.log'   SIZE 1M,
                  '/home/oracle/oradata/horde/redo02.log'   SIZE 1M,
                  '/home/oracle/oradata/horde/redo03.log'   SIZE 1M
    DATAFILE '/home/oracle/oradata/horde/system01.dbf' SIZE 10M
      AUTOEXTEND ON
      NEXT 10M MAXSIZE 512M
    ARCHIVELOG
    CHARACTER SET WE8ISO8859P1
    NATIONAL CHARACTER SET WE8ISO8859P1;

-- Create a (temporary) rollback segment in the system talbespace
CREATE ROLLBACK SEGMENT rb_temp STORAGE (INITIAL 100 k NEXT 250 k);

-- Alter temporary rollback segment online before proceding
ALTER ROLLBACK SEGMENT rb_temp ONLINE;

-- Create additional tablespaces ...
-- RBS: For rollback segments
-- USERs: Create user sets this as the default tablespace
-- TEMP: Create user sets this as the temporary tablespace
CREATE TABLESPACE rbs
    DATAFILE '/home/oracle/oradata/horde/rbs01.dbf' SIZE 5M AUTOEXTEND ON
      NEXT 5M MAXSIZE 150M;
CREATE TABLESPACE users
    DATAFILE '/home/oracle/oradata/horde/users01.dbf' SIZE 3M AUTOEXTEND ON
      NEXT 5M MAXSIZE 15M;
CREATE TABLESPACE temp
    DATAFILE '/home/oracle/oradata/horde/temp01.dbf' SIZE 2M AUTOEXTEND ON
      NEXT 5M MAXSIZE 150M;

-- Create rollback segments.
CREATE ROLLBACK SEGMENT rb1 STORAGE(INITIAL 50K NEXT 250K)
  tablespace rbs;
CREATE ROLLBACK SEGMENT rb2 STORAGE(INITIAL 50K NEXT 250K)
  tablespace rbs;
CREATE ROLLBACK SEGMENT rb3 STORAGE(INITIAL 50K NEXT 250K)
  tablespace rbs;
CREATE ROLLBACK SEGMENT rb4 STORAGE(INITIAL 50K NEXT 250K)
  tablespace rbs;

-- Bring new rollback segments online and drop the temporary system one
ALTER ROLLBACK SEGMENT rb1 ONLINE;
ALTER ROLLBACK SEGMENT rb2 ONLINE;
ALTER ROLLBACK SEGMENT rb3 ONLINE;
ALTER ROLLBACK SEGMENT rb4 ONLINE;

ALTER ROLLBACK SEGMENT rb_temp OFFLINE;
DROP ROLLBACK SEGMENT rb_temp ;

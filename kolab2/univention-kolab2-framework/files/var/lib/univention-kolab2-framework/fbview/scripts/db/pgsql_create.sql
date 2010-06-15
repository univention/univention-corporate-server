-- $Horde: horde/scripts/db/pgsql_create.sql,v 1.4 2002/06/13 13:21:25 bjn Exp $
--
-- Uncomment the ALTER line below, and change the password.  Then run as:
--
-- $ psql -d template1 -f pgsql_create.sql

CREATE DATABASE horde;

CREATE USER horde;

-- ALTER USER horde WITH PASSWORD 'pass';

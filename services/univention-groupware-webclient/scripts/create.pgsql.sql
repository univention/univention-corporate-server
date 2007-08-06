-- $Horde: horde/scripts/sql/create.pgsql.sql,v 1.1.10.1 2006/02/26 04:59:19 chuck Exp $
--
-- Uncomment the ALTER line below, and change the password.  Then run as:
--
-- $ psql -d template1 -f create.pgsql.sql

CREATE DATABASE horde;

CREATE USER horde;

-- ALTER USER horde WITH PASSWORD 'pass';

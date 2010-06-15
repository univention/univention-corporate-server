-- $ psql -d template1 -f create.database_and_user.sql

CREATE DATABASE horde;

CREATE USER horde;
-- ALTER USER horde WITH PASSWORD 'pass';

GRANT CREATE on DATABASE horde to horde;


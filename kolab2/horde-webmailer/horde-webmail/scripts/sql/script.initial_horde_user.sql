-- $Horde: horde/scripts/sql/script.initial_horde_user.sql,v 1.1.10.1 2007-12-20 15:03:03 jan Exp $
--
-- This script will create an initial user in a horde_users table. The
-- password being used is 'admin', which you should change
-- IMMEDIATELY.

-- This statement creates a user with an md5-hex password (not recommended):
-- INSERT INTO horde_users (user_uid, user_pass) VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3');

-- This statement creates a user with an SSHA-hashed password (recommended by default):
INSERT INTO horde_users (user_uid, user_pass) VALUES ('admin', 'wDa72Pg6riJ6vAYz25KbYhQ8rGqmEqEA');

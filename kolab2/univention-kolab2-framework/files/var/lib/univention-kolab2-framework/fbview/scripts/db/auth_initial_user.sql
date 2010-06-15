-- $Horde: horde/scripts/db/auth_initial_user.sql,v 1.1 2003/03/11 19:20:18 chuck Exp $
--
-- This script will create an initial user in a horde_users table. The
-- password being used is 'admin', which you should change
-- IMMEDIATELY.

INSERT INTO horde_users (user_uid, user_pass) VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3');

# $Horde: horde/scripts/db/mysql_drop.sql,v 1.3 2002/09/25 22:56:28 jan Exp $
#
# You can simply direct this file to mysql as STDIN:
#
# $ mysql --user=root --password=<MySQL-root-password> < mysql_drop.sql

USE mysql;

DELETE FROM user WHERE user LIKE 'horde%';

DELETE FROM db WHERE user LIKE 'horde%';

DROP DATABASE IF EXISTS horde;

FLUSH PRIVILEGES;

# Done!

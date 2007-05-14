#
# cron job for univention-ldap-server
#
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 0	* * *	root		/usr/sbin/univention-ldap-backup


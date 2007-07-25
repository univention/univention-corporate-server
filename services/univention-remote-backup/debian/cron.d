#
# cron job for the univention-remote-backup package
#
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

10 0	* * 2-6	root	remote-backup --servers
0 13	* * 1-5	root	remote-backup --clients

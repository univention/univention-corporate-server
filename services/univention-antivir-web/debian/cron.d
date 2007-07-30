# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
#
# cron job for the univention-antivir-web package (remove old files every 6 hours)
#
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 */6	* * *	www-data	find /var/www/downloads/ -type f -mtime +1 \! -name index.htm -exec rm -f {} \;

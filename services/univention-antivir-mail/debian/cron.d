# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
#
# cron job for the univention-antivir-mail package
# (remove old files every 6 hours)
#
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 */6	* * *	amavis	find /var/lib/amavis/virusmails/ -type f -mtime +30 -exec rm -f {} \;

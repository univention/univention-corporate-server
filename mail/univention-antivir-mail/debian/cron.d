# cron job for the univention-antivir-mail package
# (remove old files every 6 hours)
#
# SPDX-FileCopyrightText: 2001-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 */6	* * *	amavis	find /var/lib/amavis/virusmails/ -type f -mtime +30 -exec rm -f {} \;

#!/bin/sh
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
set -e

t='/var/lib/univention-ldap/notify/transaction'
if [ -s "$t" ] &&
	[ -f /var/univention-join/joined ] &&
	start-stop-daemon --status --pidfile /var/run/slapd/slapd.pid -x /usr/sbin/slapd -- -f /etc/ldap/slapd.conf &&
	last="$(awk 'END{print $1}' "$t")" &&
	! /usr/share/univention-directory-notifier/univention-translog ldap "$last" >/dev/null
then
	/usr/share/univention-directory-notifier/univention-translog --lenient import
fi

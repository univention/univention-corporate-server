#!/bin/sh
#
# SPDX-FileCopyrightText: 2007-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Test failure cases
#
set -e

univention-config-registry set directory/reports/templates/csv/user2='users/user "My CSV Report" /etc/univention/directory/reports/default/users2.csv'
tmp=$(mktemp)
cleanup () {
	[ $? -eq 0 ] || cat "$tmp"
	univention-config-registry unset directory/reports/templates/csv/user2
	rm -rf "$tmp"
}
trap cleanup EXIT

! univention-directory-reports >"$tmp" 2>&1
! grep -Fi "traceback" "$tmp"
grep -F "error: module not specified (use -m)" "$tmp"

! univention-directory-reports -m users/user >"$tmp" 2>&1
! grep -Fi "traceback" "$tmp"
grep -F "error: no DNs specified on command line" "$tmp"

! univention-directory-reports -m users/user -r "My CSV Report" >"$tmp" 2>&1
! grep -Fi "traceback" "$tmp"
grep -F "error: specified report 'My CSV Report' is unavailable" "$tmp"
grep -F "Template file '/etc/univention/directory/reports/default/users2.csv' seems to be missing." "$tmp"

univention-directory-reports -m users/user -r "Standard CSV Report" invalid >"$tmp" 2>&1
! grep -Fi "traceback" "$tmp"
grep -F "warning: dn 'invalid' not found, skipped." "$tmp"

:

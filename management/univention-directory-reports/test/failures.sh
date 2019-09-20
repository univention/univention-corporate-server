#!/bin/sh
#
# Copyright 2007-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
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

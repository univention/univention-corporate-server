#!/bin/bash
#
# Univention System Activation
#  test script
#
# Copyright 2015-2019 Univention GmbH
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

. "$TESTLIBPATH/base.sh" || exit 137

set -e

RESPONSE_CODE=0
function http {
	out=($(curl -s -w '\n%{http_code}' "$@" 'http://localhost:8398'))
	echo "${out[@]:0:${#out[@]}-1}"
	RESPONSE_CODE="${out[${#out[@]}-1]}"
}

function has_request_failed {
	[ "${RESPONSE_CODE:0:1}" != "2" ]
}

function get_license_modify_timestamp {
	univention-ldapsearch -LLL cn=admin modifyTimestamp | sed -n 's/modifyTimestamp: \([0-9]*\)Z/\1/p'
}


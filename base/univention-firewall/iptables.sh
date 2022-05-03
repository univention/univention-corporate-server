#!/bin/sh
#
# Copyright 2022 Univention GmbH
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

_checked () {
	local exe="${1:?}" table='' command='' chain='' num=''
	shift
	while [ $# -ge 1 ]
	do
		case "$1" in
		--wait) shift ;;
		-t|--table)
			table="${2:?}"
			shift 2
			;;
		-A|--append|-I|--insert)
			command="$1" chain="${2:?}"
			shift 2
			break
			;;
		*) break ;;
		esac
	done

	case "$command" in
	-I|--insert)
		case "${1:-}" in
		[0-9]*)
			num="$1"
			shift
		esac
	esac

	[ -n "$command" ] &&
		"$exe" --wait ${table:+-t "$table"} --check "$chain" "$@" 2>/dev/null &&
		return 0

	"$exe" --wait ${table:+-t "$table"} ${command:+"$command"} ${chain:+"$chain"} ${num:+"$num"} "$@"
}
iptables () { _checked /sbin/iptables "$@"; }
ip6tables () { _checked /sbin/ip6tables "$@"; }

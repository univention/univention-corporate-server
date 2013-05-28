# Univention Samba4 Shell Library (bash)
#
# Copyright 2012-2013 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.


# Bug #27001
univention_samba4_is_ucr_false () { # test if UCS variable is "false"
    local value
    value="$(univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
        1|yes|on|true|enable|enabled) return 1 ;;
        0|no|off|false|disable|disabled) return 0 ;;
        *) return 2 ;;
    esac
}

extract_binddn_and_bindpwd_from_args() {
	## parse binddn and bindpwd from command line arguments into shell variables
	while [ $# -gt 0 ]; do
		case "$1" in
			"--binddn")
							binddn="${2:?missing binddn}"
							shift 2 || exit 2
							;;
			"--bindpwd")
							bindpwd="${2:?missing bindpwd}"
							shift 2 || exit 2
							;;
			*)
				shift
				;;
		esac
	done
}

univention_samba4_append_to_ucr() {
	key="${1?append_to_ucr needs two parameters, called without any}"
	value="${2?append_to_ucr needs two parameters, called only with \""$@"\"}"
	separator=','

	python <<-%EOF
	from univention.config_registry import ConfigRegistry
	ucr = ConfigRegistry()
	ucr.load()
	valuelist = ucr.get('$key', '').split('$separator')
	if not '$value' in valuelist:
	    valuelist.append('$value')
	    ucr['$key'] = '$separator'.join(valuelist)
	    ucr.save()
	%EOF
}

create_Enterprise_Domain_Controllers() {
	## Note: This is actually joinscript code, but needs to be put here, to be called also from
	##       univention-s4-connector.postinst because the joinscript version could not be increased
	##       for the errata update.
	## Note: S4 Connector currently does not synchronize it to the Samba4 foreignSecurityPrincipal
	##       having the same builtin SID. Additionally it should be put to the group/ignorelist,
	##       as it would cause rejects.
	##
	## attempt to create group with correct builtin SID
	if /usr/share/univention-samba4/scripts/create_group_Enterprise_Domain_Controllers.py "$@"; then

		## update local group cache
		. /usr/share/univention-lib/ucr.sh
		is_ucr_true nss/group/cachefile
		if [ $? != 1 ]; then	## $? = 2 would indicate an unset variable.
			if is_ucr_true nss/group/cachefile/check_member; then
				option='--check_member'
			fi
			/usr/lib/univention-pam/ldap-group-to-file.py "${option[@]}"
		fi
	fi
}

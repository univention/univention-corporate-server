# Univention Common Shell Library
#
# Copyright 2011-2019 Univention GmbH
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

is_ucr_true () { # test if UCR variable is "true" or "false"
	local value
	value="$(/usr/sbin/univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
		1|yes|on|true|enable|enabled) return 0 ;;
		0|no|off|false|disable|disabled) return 1 ;;
		*) return 2 ;;
	esac
}

is_ucr_false () { # test if UCS variable is "false"
	local value
	value="$(/usr/sbin/univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
		1|yes|on|true|enable|enabled) return 1 ;;
		0|no|off|false|disable|disabled) return 0 ;;
		*) return 2 ;;
	esac
}


#
# DEPRECATED - will be removed UCS-4.3/5.0
# removes a UCR template and moves it to /etc/univention/templates/removed
#
# remove_ucr_template <pathname-of-config-file>
# e.g. remove_ucr_template /etc/obsolete-software.conf
#
remove_ucr_template () {
	echo "DEPRECATED: The use of 'remove_ucr_template' is broken; see Bug #27872" >&2
	[ -n "$1" ] || return 1
	if [ -f "$1" ] ; then
	    mv "$1" /etc/univention/templates/removed/
	fi
	if [ -f /etc/univention/templates/files/"$1" ] ; then
	    mv /etc/univention/templates/files/"$1" "/etc/univention/templates/removed/$(basename "$1").template.$(date +%Y%m%d_%H%M%S_%N)"
	fi
	/usr/sbin/univention-config-registry update
}

#
# DEPRECATED - will be removed UCS-4.3/5.0
# removes a UCR info file and moves it to /etc/univention/templates/removed
#
# remove_ucr_info_file <filename-of-info-file>
# e.g. remove_ucr_info_file univention-obsolete-package.info
#
remove_ucr_info_file () {
	echo "DEPRECATED: The use of 'remove_ucr_info_file' is broken; see Bug #27872" >&2
	[ -n "$1" ] || return 1
	if [ -f /etc/univention/templates/info/"$1" ] ; then
	    # unregister info file before moving
		/usr/sbin/univention-config-registry unregister "$(basename "$1" .info)"
	    mv /etc/univention/templates/info/"$1" "/etc/univention/templates/removed/$(basename "$1").$(date +%Y%m%d_%H%M%S_%N)"
	fi
}
